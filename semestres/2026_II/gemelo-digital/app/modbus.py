#!/usr/bin/env python3
"""Modbus para integrar el brazo a la red del laboratorio (guía 8). Sin dependencias.

Esclavo Modbus TCP (dentro de la app, opción --modbus): la PC del brazo publica lo que lee del PLC por PPI
como registros de retención, así un maestro Modbus (el SCADA del laboratorio u otra planta) lee el brazo
sin hablar PPI. Es una pasarela PPI -> Modbus TCP: el S7-200 sigue con su programa y su protocolo.
Solo lectura: las funciones de escritura responden con la excepción 01 (función no permitida), para que
nadie mueva el brazo desde la red industrial sin pasar por el mando y el watchdog de la app.

Mapa de registros (dirección base 40001 = registro 0; enteros de 32 bits: palabra alta primero):

    40001-40002  ZI-101   posición de la base [pulsos, int32]
    40003-40004  ZI-102   posición del carro X [pulsos, int32]
    40005-40006  ZI-103   posición del carro Y [pulsos, int32]
    40007        SY-100   frecuencia del tren X/Y [Hz]
    40008        SY-101   frecuencia del tren de la base [Hz]
    40009        --       entradas: bit 0 = I0.0 ... bit 7 = I0.7, bit 8 = I1.0 ... bit 13 = I1.5
    40010        --       salidas: bit 0 = Q0.0 ... bit 7 = Q0.7
    40011        ZI-101   base [0,1 grados, int16]
    40012        ZI-102   carro X [0,1 mm]
    40013        ZI-103   carro Y [0,1 mm]
    40014        --       estado: bit 0 conectado, 1 referenciado, 2 en movimiento, 3 garra cerrada,
                          4 modo automático, 5 error del PLC
    40015        --       contador de lecturas del PLC (cambia si la pasarela está viva)

Cliente (prueba de la red y estadísticas de tramas, guía 8 tarea 59):

    python3 modbus.py cliente --tcp 127.0.0.1:5020 --repetir 100
    python3 modbus.py cliente --rtu /dev/ttyUSB0 --baudios 9600 --esclavo 1 --repetir 100   (S7-200 con MBUS_SLAVE)
    python3 modbus.py simular --puerto 5020          (esclavo con el PLC simulado de la app, para probar sin planta)
"""
import argparse
import socket
import socketserver
import struct
import sys
import threading
import time

N_REGISTROS = 15
EXCEPCIONES = {1: 'función no permitida', 2: 'dirección no permitida', 3: 'valor no permitido', 4: 'falla del esclavo'}


# ====================================================================== CRC y tramas
def crc16(datos):
    """CRC-16/MODBUS (polinomio 0xA001 reflejado, valor inicial 0xFFFF); se envía byte bajo primero."""
    crc = 0xFFFF
    for b in datos:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def trama_rtu(esclavo, pdu):
    cuerpo = bytes([esclavo]) + pdu
    return cuerpo + struct.pack('<H', crc16(cuerpo))


def registros(e, lecturas=0):
    """Estado de la app (Brazo.leer_estado()) -> lista de 15 registros de 16 bits."""
    r = [0] * N_REGISTROS
    if not e:
        return r
    p = e.get('pulsos') or {}
    for i, eje in enumerate(('Z', 'X', 'Y')):
        v = int(p.get(eje) or 0) & 0xFFFFFFFF
        r[2 * i], r[2 * i + 1] = v >> 16, v & 0xFFFF
    f = e.get('f_hz') or {}
    r[6], r[7] = min(int(f.get('xy') or 0), 65535), min(int(f.get('base') or 0), 65535)
    ent, sal = e.get('entradas') or {}, e.get('salidas') or {}
    r[8] = sum(1 << (8 * int(k[1]) + int(k[3])) for k, v in ent.items() if v)
    r[9] = sum(1 << int(k[3]) for k, v in sal.items() if v)
    for i, clave in enumerate(('theta_deg', 'sX_mm', 'sY_mm')):
        r[10 + i] = int(round((e.get(clave) or 0) * 10)) & 0xFFFF
    bits = [e.get('conectado'), e.get('referenciado'), e.get('en_movimiento'), e.get('garra'), e.get('modo_auto'),
            bool((e.get('plc') or {}).get('error'))]
    r[13] = sum(1 << i for i, b in enumerate(bits) if b)
    r[14] = lecturas & 0xFFFF
    return r


def decodificar(r):
    s32 = lambda hi, lo: struct.unpack('>i', struct.pack('>HH', hi, lo))[0]
    s16 = lambda v: v - 65536 if v > 32767 else v
    return {'pulsos_base': s32(r[0], r[1]), 'pulsos_x': s32(r[2], r[3]), 'pulsos_y': s32(r[4], r[5]),
            'f_xy_hz': r[6], 'f_base_hz': r[7], 'entradas': f'{r[8]:014b}'[::-1], 'salidas': f'{r[9]:08b}'[::-1],
            'theta_deg': s16(r[10]) / 10, 'sX_mm': s16(r[11]) / 10, 'sY_mm': s16(r[12]) / 10,
            'estado': {n: bool(r[13] >> i & 1) for i, n in enumerate(
                ('conectado', 'referenciado', 'en_movimiento', 'garra', 'modo_auto', 'error'))},
            'contador': r[14]}


def responder(pdu, regs):
    """PDU de petición -> PDU de respuesta (lógica común a TCP y RTU)."""
    if not pdu:
        return None
    fc = pdu[0]
    if fc in (3, 4):
        if len(pdu) != 5:
            return bytes([fc | 0x80, 3])
        inicio, n = struct.unpack('>HH', pdu[1:5])
        if not 1 <= n <= 125:
            return bytes([fc | 0x80, 3])
        if inicio + n > len(regs):
            return bytes([fc | 0x80, 2])
        return bytes([fc, 2 * n]) + struct.pack(f'>{n}H', *regs[inicio:inicio + n])
    return bytes([fc | 0x80, 1])          # escrituras y demás funciones: no permitidas (solo lectura)


# ====================================================================== esclavo TCP (pasarela)
class ServidorModbus:
    def __init__(self, obtener_brazo, puerto=5020, registrar=print, direccion='0.0.0.0'):
        self.obtener_brazo = obtener_brazo
        self.estadisticas = {'peticiones': 0, 'excepciones': 0, 'tramas_malas': 0, 'clientes': 0}
        self.lock = threading.Lock()
        servidor = self

        class Manejador(socketserver.BaseRequestHandler):
            def handle(self):
                with servidor.lock:
                    servidor.estadisticas['clientes'] += 1
                self.request.settimeout(60)
                buf = b''
                while True:
                    try:
                        datos = self.request.recv(260)
                    except (OSError, socket.timeout):
                        return
                    if not datos:
                        return
                    buf += datos
                    while len(buf) >= 7:
                        tid, proto, largo = struct.unpack('>HHH', buf[:6])
                        if proto != 0 or not 2 <= largo <= 254:
                            with servidor.lock:
                                servidor.estadisticas['tramas_malas'] += 1
                            return
                        if len(buf) < 6 + largo:
                            break
                        unidad, pdu, buf = buf[6], buf[7:6 + largo], buf[6 + largo:]
                        resp = servidor.atender(pdu)
                        self.request.sendall(struct.pack('>HHHB', tid, 0, len(resp) + 1, unidad) + resp)

        socketserver.ThreadingTCPServer.allow_reuse_address = True
        self.srv = socketserver.ThreadingTCPServer((direccion, puerto), Manejador)
        self.srv.daemon_threads = True
        self.puerto = puerto
        threading.Thread(target=self.srv.serve_forever, daemon=True, name='modbus').start()
        registrar(f'Modbus TCP: esclavo en el puerto {puerto} (solo lectura, registros 40001-400{N_REGISTROS:02d})')

    def atender(self, pdu):
        b = self.obtener_brazo()
        regs = registros(b.leer_estado() if b else None, b.lecturas if b else 0)
        resp = responder(pdu, regs)
        with self.lock:
            self.estadisticas['peticiones'] += 1
            if resp[0] & 0x80:
                self.estadisticas['excepciones'] += 1
        return resp

    def info(self):
        with self.lock:
            return dict(self.estadisticas, puerto=self.puerto)

    def cerrar(self):
        self.srv.shutdown()
        self.srv.server_close()


# ====================================================================== maestro (cliente)
class ErrorModbus(IOError):
    pass


class MaestroTCP:
    def __init__(self, host, puerto=502, unidad=1, espera=1.0):
        self.s = socket.create_connection((host, puerto), timeout=espera)
        self.unidad, self.tid = unidad, 0

    def leer(self, inicio, n, fc=3):
        self.tid = (self.tid + 1) & 0xFFFF
        pdu = struct.pack('>BHH', fc, inicio, n)
        self.s.sendall(struct.pack('>HHHB', self.tid, 0, len(pdu) + 1, self.unidad) + pdu)
        cab = self._exacto(7)
        tid, _, largo, _ = struct.unpack('>HHHB', cab)
        resp = self._exacto(largo - 1)
        if tid != self.tid:
            raise ErrorModbus('respuesta de otra transacción')
        return _registros_de(resp, fc, n)

    def _exacto(self, n):
        d = b''
        while len(d) < n:
            parte = self.s.recv(n - len(d))
            if not parte:
                raise ErrorModbus('el esclavo cerró la conexión')
            d += parte
        return d

    def cerrar(self):
        self.s.close()


class MaestroRTU:
    """Maestro RTU por RS-485 (8 bits, paridad par, 1 parada: configurar igual MBUS_INIT en el S7-200)."""

    def __init__(self, puerto, baudios=9600, esclavo=1, espera=0.5):
        sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
        import serie
        self.p = serie.Puerto(puerto, baudios)
        self.p.abrir()
        self.esclavo, self.espera, self.baudios = esclavo, espera, baudios

    def leer(self, inicio, n, fc=3):
        self.p.vaciar_entrada()
        self.p.escribir(trama_rtu(self.esclavo, struct.pack('>BHH', fc, inicio, n)))
        esperado = 5 + 2 * n
        d, fin = b'', time.time() + self.espera
        while time.time() < fin and len(d) < esperado:
            d += self.p.leer()
            if len(d) >= 5 and d[1] & 0x80:
                break
        if not d:
            raise TimeoutError('sin respuesta del esclavo')
        largo = 5 if len(d) >= 2 and d[1] & 0x80 else esperado
        if len(d) < largo:
            raise ErrorModbus(f'trama incompleta ({len(d)} de {largo} bytes)')
        d = d[:largo]
        if crc16(d[:-2]) != struct.unpack('<H', d[-2:])[0]:
            raise ValueError('CRC incorrecto')
        if d[0] != self.esclavo:
            raise ErrorModbus(f'respondió el esclavo {d[0]}')
        return _registros_de(d[1:-2], fc, n)

    def cerrar(self):
        self.p.cerrar()


def _registros_de(resp, fc, n):
    if resp[0] == fc | 0x80:
        raise ErrorModbus(f'excepción {resp[1]}: {EXCEPCIONES.get(resp[1], "?")}')
    if resp[0] != fc or resp[1] != 2 * n:
        raise ErrorModbus('respuesta mal formada')
    return list(struct.unpack(f'>{n}H', resp[2:2 + 2 * n]))


def cliente(a):
    if a.tcp:
        host, _, puerto = a.tcp.partition(':')
        m = MaestroTCP(host, int(puerto or 502), a.esclavo)
    else:
        m = MaestroRTU(a.rtu, a.baudios, a.esclavo)
    est = {'ok': 0, 'sin_respuesta': 0, 'crc': 0, 'excepcion_u_otra': 0}
    tiempos, ultimo = [], None
    try:
        for i in range(a.repetir):
            t0 = time.perf_counter()
            try:
                ultimo = m.leer(0, N_REGISTROS)
                est['ok'] += 1
                tiempos.append((time.perf_counter() - t0) * 1000)
            except TimeoutError:
                est['sin_respuesta'] += 1
            except ValueError:
                est['crc'] += 1
            except (ErrorModbus, OSError) as ex:
                est['excepcion_u_otra'] += 1
                if i == 0:
                    print('error:', ex)
            if a.pausa:
                time.sleep(a.pausa)
    finally:
        m.cerrar()
    if ultimo:
        for k, v in decodificar(ultimo).items():
            print(f'  {k:14s} {v}')
    total = a.repetir
    print(f'\nPeticiones: {total}  correctas: {est["ok"]}  sin respuesta: {est["sin_respuesta"]}  '
          f'CRC incorrecto: {est["crc"]}  otras: {est["excepcion_u_otra"]}  '
          f'tasa de error: {100 * (total - est["ok"]) / total:.2f} %')
    if tiempos:
        tiempos.sort()
        print(f'Tiempo de respuesta [ms]: mínimo {tiempos[0]:.2f}  mediana {tiempos[len(tiempos) // 2]:.2f}  '
              f'máximo {tiempos[-1]:.2f}')
    return est


def simular(a):
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from brazo import Brazo
    b = Brazo(simulado=True)
    ServidorModbus(lambda: b, a.puerto)
    print('PLC simulado; Ctrl+C para salir')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def main():
    ap = argparse.ArgumentParser(description='Modbus del brazo XK-JS1-1: cliente de prueba y esclavo simulado')
    sub = ap.add_subparsers(dest='orden', required=True)
    c = sub.add_parser('cliente', help='leer los registros 40001-40015 y medir la tasa de error')
    g = c.add_mutually_exclusive_group(required=True)
    g.add_argument('--tcp', help='esclavo Modbus TCP, host:puerto')
    g.add_argument('--rtu', help='puerto serie del adaptador RS-485 (COM5, /dev/ttyUSB0)')
    c.add_argument('--baudios', type=int, default=9600)
    c.add_argument('--esclavo', type=int, default=1)
    c.add_argument('--repetir', type=int, default=1)
    c.add_argument('--pausa', type=float, default=0.0, help='s entre peticiones')
    s = sub.add_parser('simular', help='esclavo Modbus TCP con el PLC simulado')
    s.add_argument('--puerto', type=int, default=5020)
    a = ap.parse_args()
    cliente(a) if a.orden == 'cliente' else simular(a)


if __name__ == '__main__':
    main()
