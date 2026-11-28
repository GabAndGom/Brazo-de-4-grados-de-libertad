#!/usr/bin/env python3
"""PI discreto de un eje del brazo (guía 6): diseño, simulación y prueba de lazo flotante.

    python3 pi_discreto.py diseno                      -> b0, b1, respuesta simulada y figura
    python3 pi_discreto.py flotante --simulado         -> prueba de lazo flotante contra el emulador de la rutina
    python3 pi_discreto.py flotante --puerto COM3      -> la misma prueba contra el PLC real (app CERRADA,
                                                          programa con gemelo-digital/plc/pi_lazo_flotante.awl,
                                                          drivers DESENERGIZADOS)

Planta (laboratorios 4 y 5): un carro es un integrador, G(z) = b Ts / (z - 1), b = 1/200 mm/(Hz s).
Controlador: D(z) = (b0 z + b1) / (z - 1)  ->  u(k) = u(k-1) + b0 e(k) + b1 e(k-1).
Lazo cerrado: z^2 + (b Ts b0 - 2) z + (1 + b Ts b1) = 0. Con dos polos en p (reales, amortiguamiento
crítico): b0 = (2 - 2p) / (b Ts), b1 = (p^2 - 1) / (b Ts).

La prueba de lazo flotante (tarea 40 del docente) ejecuta la rutina de interrupción paso a paso con un
error simulado y compara la acción u(k) que calcula el PLC con la que da esta ecuación: si coinciden, la
ecuación de diferencias está bien programada y se puede habilitar el actuador. El emulador usa REAL de
32 bits como el S7-200.
"""
import argparse
import csv
import os
import struct
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
APP = os.path.abspath(os.path.join(AQUI, '..', '..', 'gemelo-digital', 'app'))
B = 1 / 200            # mm/(Hz s): 200 pulsos/mm (husillo de 5 mm, SUPUESTO)
TS = 0.025             # s, SMB34 = 25
U_MAX = 5000.0         # Hz, máximo probado sin pérdida de pasos
POLO = 0.9             # polo doble de lazo cerrado (constante de tiempo Ts / -ln 0.9 = 0,24 s)
# memoria de pi_lazo_flotante.awl
V_R, V_Y, V_E, V_E1, V_U, V_U1, V_B0, V_B1, V_MODO, V_K, V_PASOS = \
    1300, 1304, 1308, 1312, 1316, 1320, 1324, 1328, 1332, 1334, 1336


def ganancias(p=POLO, b=B, ts=TS):
    h = b * ts
    return (2 - 2 * p) / h, (p * p - 1) / h


def f32(x):
    return struct.unpack('>f', struct.pack('>f', x))[0]


class RutinaINT:
    """Emulador de INT0 de pi_lazo_flotante.awl con aritmética REAL de 32 bits."""

    def __init__(self, b0, b1):
        self.b0, self.b1 = f32(b0), f32(b1)
        self.e1 = self.u1 = 0.0
        self.k = 0

    def paso(self, r, y):
        e = f32(f32(r) - f32(y))
        u = f32(f32(self.u1 + f32(self.b0 * e)) + f32(self.b1 * self.e1))
        u = max(-U_MAX, min(U_MAX, u))
        self.e1, self.u1, self.k = e, u, self.k + 1
        return e, u


def simular(b0, b1, ref=10.0, n=120, perturbacion=0.0):
    """Lazo cerrado con la planta integradora; perturbacion: mm/s de deriva (p. ej. pasos perdidos)."""
    pi = RutinaINT(b0, b1)
    x, t, xs, us = 0.0, [], [], []
    for k in range(n):
        _, u = pi.paso(ref, x)
        t.append(k * TS)
        xs.append(x)
        us.append(u)
        x += TS * (B * u - perturbacion)
    return np.array(t), np.array(xs), np.array(us)


def diseno(a):
    b0, b1 = ganancias(a.polo)
    print(f'Planta: G(z) = {B * TS:.3e} / (z - 1)   (b = {B} mm/(Hz s), Ts = {TS * 1000:.0f} ms)')
    print(f'Polos de lazo cerrado: {a.polo} (doble)  ->  b0 = {b0:.1f} Hz/mm   b1 = {b1:.1f} Hz/mm')
    print(f'Equivalente continuo: Kp = {-b1:.1f} Hz/mm, Ki = {(b0 + b1) / TS:.1f} Hz/(mm s)')
    raices = np.roots([1, B * TS * b0 - 2, 1 + B * TS * b1])
    print(f'Verificación: raíces del polinomio característico = {np.round(raices, 4)}')
    filas = []
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 5.5), sharex=True)
    for ref in (1.0, 10.0, 50.0):
        t, x, u = simular(b0, b1, ref, n=int(8 / TS))
        sobre = max(0.0, (x.max() - ref) / ref * 100)
        t95 = t[np.argmax(np.abs(x - ref) <= 0.05 * ref)] if np.any(np.abs(x - ref) <= 0.05 * ref) else float('nan')
        sat = 100 * np.mean(np.abs(u) >= U_MAX - 1e-3)
        filas.append((ref, sobre, t95, sat))
        ax1.plot(t, x / ref, label=f'escalón de {ref:g} mm')
        ax2.plot(t, u, label=f'{ref:g} mm')
    print(f'\n{"escalón [mm]":>12s} {"sobreimpulso [%]":>17s} {"t 5 % [s]":>10s} {"tiempo saturado [%]":>20s}')
    for ref, s, t95, sat in filas:
        print(f'{ref:12.1f} {s:17.2f} {t95:10.3f} {sat:20.1f}')
    ax1.axhline(1, color='k', lw=.6)
    ax1.set_ylabel('posición / referencia')
    ax1.legend()
    ax1.grid(alpha=.3)
    ax2.set_ylabel('u(k) [Hz]')
    ax2.set_xlabel('t [s]')
    ax2.grid(alpha=.3)
    ax1.set_title(f'PI discreto (polos en {a.polo}, Ts = 25 ms) sobre el modelo del carro, con saturación a 5 kHz',
                  fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(AQUI, 'pi_respuesta_simulada.png'), dpi=150)
    print('Figura: pi_respuesta_simulada.png  (SIMULACIÓN: la planta real no tiene sensor de posición)')


def perfil_error():
    """Error simulado para la prueba de lazo flotante: escalones y una rampa (60 pasos)."""
    return [1.0] * 10 + [0.0] * 10 + [-2.0] * 10 + [0.5 * i for i in range(10)] + [0.0] * 10 + [20.0] * 10


class PLCPorPPI:
    def __init__(self, puerto, direccion, baudios):
        sys.path.insert(0, APP)
        from ppi import ClientePPI, buscar_plc
        if direccion is None:
            r = buscar_plc(puerto)
            if not r:
                raise SystemExit(f'no responde ningún PLC en {puerto}')
            direccion, baudios = r
        self.c = ClientePPI(puerto, plc=direccion, baudios=baudios, zonas_escritura=[('V', 1300, 1337)])
        self.c.abrir()

    def real(self, v, x):
        self.c.escribir('V', v, struct.pack('>f', x))

    def leer_real(self, v):
        return struct.unpack('>f', self.c.leer('V', v, 4))[0]

    def byte(self, v, x):
        self.c.escribir('V', v, bytes([x]))

    def palabra(self, v, x):
        self.c.escribir('V', v, struct.pack('>H', x))

    def leer_palabra(self, v):
        return struct.unpack('>H', self.c.leer('V', v, 2))[0]

    def cerrar(self):
        self.c.cerrar()


class PLCEmulado(PLCPorPPI):
    """La misma memoria que el PLC, con la rutina emulada: para probar este script sin planta."""

    def __init__(self):
        self.v = {}
        self.rutina = None

    def real(self, v, x):
        self.v[v] = f32(x)

    def leer_real(self, v):
        return self.v.get(v, 0.0)

    def byte(self, v, x):
        self.v[v] = x

    def palabra(self, v, x):
        self.v[v] = x
        if v == V_PASOS:                     # la «interrupción» ejecuta los pasos pedidos
            if self.rutina is None:
                self.rutina = RutinaINT(self.v[V_B0], self.v[V_B1])
            for _ in range(x):
                e, u = self.rutina.paso(self.v.get(V_R, 0.0), self.v.get(V_Y, 0.0))
                self.v[V_E], self.v[V_U] = e, u
            self.v[V_PASOS], self.v[V_K] = 0, self.rutina.k

    def leer_palabra(self, v):
        return self.v.get(v, 0)

    def cerrar(self):
        pass


def flotante(a):
    b0, b1 = ganancias(a.polo)
    plc = PLCEmulado() if a.simulado else PLCPorPPI(a.puerto, a.direccion, a.baudios)
    esperado = RutinaINT(b0, b1)
    try:
        plc.byte(V_MODO, 0)
        for v, x in ((V_B0, b0), (V_B1, b1), (V_R, 0.0), (V_Y, 0.0), (V_E, 0.0), (V_E1, 0.0), (V_U, 0.0),
                     (V_U1, 0.0)):
            plc.real(v, x)
        plc.palabra(V_PASOS, 0)
        plc.byte(V_MODO, 1)
        filas, peor = [], 0.0
        for k, e_sim in enumerate(perfil_error()):
            plc.real(V_Y, -e_sim)                  # r = 0, y = -e  ->  e = e_sim
            plc.palabra(V_PASOS, 1)
            t0 = time.time()
            while plc.leer_palabra(V_PASOS) != 0:
                if time.time() - t0 > 2:
                    raise SystemExit('el PLC no ejecutó el paso: ¿está cargada la rutina INT0 y SMB34 = 25?')
                time.sleep(0.01)
            u_plc = plc.leer_real(V_U)
            _, u_esp = esperado.paso(0.0, -e_sim)
            dif = abs(u_plc - u_esp)
            peor = max(peor, dif)
            filas.append({'k': k, 'e_simulado_mm': e_sim, 'u_plc_hz': round(u_plc, 3), 'u_esperado_hz': round(u_esp, 3),
                          'diferencia_hz': round(dif, 4)})
        plc.byte(V_MODO, 0)
    finally:
        plc.cerrar()
    nombre = 'lazo_flotante_' + ('EMULADO' if a.simulado else time.strftime('PLC_%Y%m%d_%H%M%S')) + '.csv'
    with open(os.path.join(AQUI, nombre), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(f'b0 = {b0:.1f}, b1 = {b1:.1f} Hz/mm; {len(filas)} pasos; diferencia máxima |u_PLC - u_esperado| = '
          f'{peor:.4f} Hz -> {"APROBADO" if peor < 0.5 else "REVISAR la rutina"}')
    print('Registro:', nombre)
    for fila in filas[:12]:
        print('  ', fila)


def main():
    ap = argparse.ArgumentParser(description='PI discreto de un carro del brazo (guía 6)')
    ap.add_argument('--polo', type=float, default=POLO, help='polo doble de lazo cerrado (0 < p < 1)')
    sub = ap.add_subparsers(dest='orden', required=True)
    sub.add_parser('diseno')
    f = sub.add_parser('flotante')
    g = f.add_mutually_exclusive_group(required=True)
    g.add_argument('--simulado', action='store_true', help='contra el emulador de la rutina')
    g.add_argument('--puerto', help='puerto del cable USB-PPI (la app debe estar cerrada)')
    f.add_argument('--direccion', type=int)
    f.add_argument('--baudios', type=int, default=9600)
    a = ap.parse_args()
    diseno(a) if a.orden == 'diseno' else flotante(a)


if __name__ == '__main__':
    main()
