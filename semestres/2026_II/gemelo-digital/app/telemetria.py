"""Registrador de telemetría: guarda lo que lee la app del PLC en CSV y en PostgreSQL (laboratorio 6).

Corre en su propio hilo, para que una base lenta o caída no frene la lectura del PLC ni el watchdog:
la lectura PPI (brazo.py) sigue a su ritmo y este hilo toma el último estado una vez por segundo.

  CSV         siempre: telemetria/telemetria_AAAAMMDD_HHMMSS.csv (una fila por segundo)
  PostgreSQL  si está instalado psycopg y hay una base brazo4gdl creada con database/scripts/brazo_4gdl.sql:
              ciclo_operacion (uno por modo elegido), muestra (ZI-101..103, SY-100/101), estado_io (cambios de
              las señales), evento_alarma (errores del PLC y pérdida de comunicación), orden y sesion.

La conexión se toma de la variable de entorno BRAZO_PG o de base_datos.json ({"conninfo": "..."});
por defecto "dbname=brazo4gdl" (usuario del sistema, sin contraseña, como queda tras instalar PostgreSQL).
Las sentencias son parametrizadas: ningún dato se pega dentro del texto SQL.
"""
import csv
import json
import os
import queue
import threading
import time
from datetime import datetime, timezone

try:
    import psycopg
except ImportError:                       # la app funciona igual: solo guarda CSV
    psycopg = None

APP = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(APP, 'telemetria')
CONFIG = os.path.join(APP, 'base_datos.json')
PERIODO = 1.0                             # s: una muestra por segundo y por variable

# variable (tag ISA) -> cómo se obtiene del estado de la app
VARIABLES = {'ZI-101': lambda e: e.get('theta_deg'), 'ZI-102': lambda e: e.get('sX_mm'),
             'ZI-103': lambda e: e.get('sY_mm'),
             'SY-101': lambda e: (e.get('f_hz') or {}).get('base'), 'SY-100': lambda e: (e.get('f_hz') or {}).get('xy')}
# texto de error del PLC -> código de alarma de la tabla alarma
ALARMAS = {'watchdog': 'watchdog', 'paro': 'paro', 'fuera del recorrido': 'fuera_de_rango',
           'homing': 'sin_homing', 'ocupado': 'ocupado'}
TIPOS_ORDEN = ('homing', 'mover', 'garra', 'detener', 'velocidad', 'iniciar', 'emergencia', 'rearmar', 'mando')


def conninfo():
    if os.environ.get('BRAZO_PG'):
        return os.environ['BRAZO_PG']
    try:
        with open(CONFIG, encoding='utf-8') as f:
            return json.load(f)['conninfo']
    except (OSError, ValueError, KeyError):
        return 'dbname=brazo4gdl'


def ahora():
    return datetime.now(timezone.utc)


class Registrador:
    def __init__(self, obtener_brazo, registrar):
        self.obtener_brazo = obtener_brazo        # función: devuelve el Brazo actual (cambia con el modo)
        self.registrar = registrar
        self.modo = None
        self.cola = queue.Queue(maxsize=5000)     # eventos (órdenes, sesiones, cambio de modo) para la base
        self.db = None
        self.ciclo = None
        self.ids = {}
        self.estado_db = 'sin conectar'
        self.filas_csv = 0
        self.muestras_db = 0
        self.ruta_csv = None
        self._csv = self._escritor = None
        self._prev_io = {}
        self._prev_alarma = None
        self._prev_conectado = None
        self._t_reintento = 0
        self.vivo = True
        threading.Thread(target=self._bucle, daemon=True, name='registrador').start()

    # ---------------------------------------------------------------- interfaz (la llama la app)
    def nuevo_modo(self, modo):
        self.cola.put(('modo', modo, ahora()))

    def orden(self, nombre, datos, quien, aceptada, motivo=None):
        self._poner(('orden', nombre, dict(datos or {}), quien, aceptada, motivo, ahora()))

    def sesion(self, usuario, ip, exito):
        self._poner(('sesion', usuario, ip, exito, ahora()))

    def info(self):
        return {'csv': os.path.relpath(self.ruta_csv, APP) if self.ruta_csv else None, 'filas_csv': self.filas_csv,
                'base_datos': self.estado_db, 'muestras_db': self.muestras_db, 'ciclo': self.ciclo,
                'psycopg': psycopg is not None}

    def cerrar(self):
        self.cola.put(('fin', ahora()))
        time.sleep(1.5)
        self.vivo = False

    def _poner(self, ev):
        try:
            self.cola.put_nowait(ev)
        except queue.Full:
            pass

    # ---------------------------------------------------------------- base de datos
    def _conectar(self):
        if psycopg is None:
            self.estado_db = 'no disponible: instale psycopg (pip install "psycopg[binary]")'
            return False
        if time.time() < self._t_reintento:
            return False
        try:
            self.db = psycopg.connect(conninfo(), autocommit=True, connect_timeout=3)
            cur = self.db.cursor()
            self.ids['variable'] = dict(cur.execute('SELECT tag_isa, id FROM variable').fetchall())
            self.ids['punto'] = dict(cur.execute('SELECT direccion, id FROM punto_io').fetchall())
            self.ids['alarma'] = dict(cur.execute('SELECT codigo, id FROM alarma').fetchall())
            self.ids['programa'] = dict(cur.execute('SELECT perfil_app, id FROM programa_plc').fetchall())
            self.ids['eje'] = dict(cur.execute('SELECT codigo, id FROM eje').fetchall())
            self.ids['sistema'] = cur.execute('SELECT id FROM sistema ORDER BY id LIMIT 1').fetchone()[0]
            # Ciclos que quedaron abiertos (la app se cerró de golpe o se cortó la luz): se cierran en su
            # último dato registrado, para no contar como operación el tiempo que la app estuvo apagada
            n = cur.execute(
                'UPDATE ciclo_operacion c SET fin = greatest(c.inicio, coalesce('
                '  (SELECT max(instante) FROM muestra WHERE ciclo_id = c.id),'
                '  (SELECT max(instante) FROM estado_io WHERE ciclo_id = c.id), c.inicio)) '
                'WHERE c.fin IS NULL AND c.sistema_id = %s', (self.ids['sistema'],)).rowcount
            if n:
                self.registrar(f'telemetría: {n} ciclo(s) abiertos de una sesión anterior cerrados en su último dato')
            self.estado_db = 'conectada'
            self.registrar('telemetría: conectada a PostgreSQL')
            if self.modo:
                self._abrir_ciclo(self.modo, ahora())
            return True
        except Exception as ex:                   # base no creada, servicio apagado, sin permisos...
            self._caida(ex)
            return False

    def _caida(self, ex):
        if self.db:
            try:
                self.db.close()
            except Exception:
                pass
        self.db, self.ciclo = None, None
        texto = str(ex).strip().splitlines()[0] if str(ex).strip() else type(ex).__name__
        if self.estado_db != 'error: ' + texto:
            self.registrar(f'telemetría: sin PostgreSQL ({texto}); se sigue guardando en CSV')
        self.estado_db = 'error: ' + texto
        self._t_reintento = time.time() + 30

    def _sql(self, sentencia, parametros=()):
        if not self.db:
            return None
        try:
            return self.db.execute(sentencia, parametros)
        except psycopg.OperationalError as ex:
            self._caida(ex)
        except psycopg.Error as ex:               # dato rechazado por una regla: se anota y se sigue
            self.registrar(f'telemetría: la base rechazó un dato ({str(ex).splitlines()[0]})')
        return None

    def _abrir_ciclo(self, modo, t):
        if self.ciclo:
            self._sql('UPDATE ciclo_operacion SET fin = %s WHERE id = %s', (t, self.ciclo))
            self.ciclo = None
        b = self.obtener_brazo()
        programa = self.ids['programa'].get(b.perfil.nombre) if b and b.perfil else None
        r = self._sql('INSERT INTO ciclo_operacion (sistema_id, programa_id, modo, inicio) VALUES (%s, %s, %s, %s) '
                      'RETURNING id', (self.ids['sistema'], programa, modo, t))
        if r:
            self.ciclo = r.fetchone()[0]
            self._prev_io = {}

    def _usuario_id(self, nombre):
        r = self._sql('SELECT id FROM usuario WHERE nombre = %s', (nombre,))
        fila = r.fetchone() if r else None
        return fila[0] if fila else None

    def _evento(self, ev):
        tipo = ev[0]
        if tipo == 'modo':
            self.modo = ev[1]
            self._abrir_csv()
            if self.db:
                self._abrir_ciclo(ev[1], ev[2])
        elif tipo == 'fin':
            if self.db and self.ciclo:
                self._sql('UPDATE ciclo_operacion SET fin = %s WHERE id = %s', (ev[1], self.ciclo))
        elif tipo == 'sesion' and self.db:
            _, usuario, ip, exito, t = ev
            self._sql('INSERT INTO sesion (usuario_id, nombre_usado, ip, instante, exito) VALUES (%s, %s, %s, %s, %s)',
                      (self._usuario_id(usuario), usuario[:32], ip, t, exito))
        elif tipo == 'orden' and self.db and self.ciclo:
            _, nombre, datos, quien, aceptada, motivo, t = ev
            if nombre not in TIPOS_ORDEN:
                return
            r = self._sql('INSERT INTO orden (ciclo_id, usuario_id, instante, tipo, aceptada, motivo) '
                          'VALUES (%s, %s, %s, %s, %s, %s) RETURNING id',
                          (self.ciclo, None if quien == 'local' else self._usuario_id(quien), t, nombre, aceptada,
                           (motivo or None) and str(motivo)[:200]))
            if r and nombre == 'mover':
                oid = r.fetchone()[0]
                for clave, eje in (('theta', 'Z'), ('sX', 'X'), ('sY', 'Y')):
                    if clave in datos and eje in self.ids['eje']:
                        self._sql('INSERT INTO orden_parametro (orden_id, eje_id, valor) VALUES (%s, %s, %s)',
                                  (oid, self.ids['eje'][eje], float(datos[clave])))

    # ---------------------------------------------------------------- CSV
    def _abrir_csv(self):
        if self._csv:
            self._csv.close()
        os.makedirs(CARPETA, exist_ok=True)
        self.ruta_csv = os.path.join(CARPETA, time.strftime('telemetria_%Y%m%d_%H%M%S.csv'))
        self._csv = open(self.ruta_csv, 'w', newline='', encoding='utf-8')
        self._escritor = csv.writer(self._csv)
        self._escritor.writerow(['instante_utc', 'modo', 'conectado', 'theta_deg', 'sX_mm', 'sY_mm', 'f_base_hz',
                                 'f_xy_hz', 'pulsos_base', 'pulsos_x', 'pulsos_y', 'en_movimiento', 'referenciado',
                                 'garra', 'entradas', 'salidas', 'error_plc'])
        self.filas_csv = 0

    def _fila_csv(self, t, e):
        if not self._escritor:
            return
        p = e.get('pulsos') or {}
        f = e.get('f_hz') or {}
        bits = lambda d: ''.join('1' if d[k] else '0' for k in sorted(d)) if d else ''
        self._escritor.writerow([t.isoformat(timespec='milliseconds'), self.modo, int(bool(e.get('conectado'))),
                                 _r(e.get('theta_deg')), _r(e.get('sX_mm')), _r(e.get('sY_mm')), f.get('base', ''),
                                 f.get('xy', ''), p.get('Z', ''), p.get('X', ''), p.get('Y', ''),
                                 int(bool(e.get('en_movimiento'))), int(bool(e.get('referenciado'))),
                                 int(bool(e.get('garra'))), bits(e.get('entradas')), bits(e.get('salidas')),
                                 (e.get('plc') or {}).get('error', '')])
        self._csv.flush()
        self.filas_csv += 1

    # ---------------------------------------------------------------- muestreo
    def _muestra(self, t, e):
        if not self.db or not self.ciclo:
            return
        if e.get('conectado') and e.get('referenciado'):
            for tag, leer in VARIABLES.items():
                v = leer(e)
                if v is not None and tag in self.ids['variable']:
                    r = self._sql('INSERT INTO muestra (ciclo_id, variable_id, instante, valor) VALUES (%s, %s, %s, %s)',
                                  (self.ciclo, self.ids['variable'][tag], t, float(v)))
                    if r is not None and r.rowcount:       # 0 filas: el trigger la descartó por fuera de rango
                        self.muestras_db += 1
        senales = dict(e.get('entradas') or {}, **(e.get('salidas') or {}))
        for dir_, valor in senales.items():
            if dir_ in self.ids['punto'] and self._prev_io.get(dir_) != valor:
                self._sql('INSERT INTO estado_io (ciclo_id, punto_id, instante, valor) VALUES (%s, %s, %s, %s)',
                          (self.ciclo, self.ids['punto'][dir_], t, bool(valor)))
                self._prev_io[dir_] = valor
        # alarmas: error del PLC y comunicación
        error = (e.get('plc') or {}).get('error') or ''
        codigo = next((c for k, c in ALARMAS.items() if k in error), None) if error else None
        if codigo != self._prev_alarma:
            if self._prev_alarma:
                self._alarma(self._prev_alarma, t, False, 'despejada')
            if codigo:
                self._alarma(codigo, t, True, error)
            self._prev_alarma = codigo
        conectado = bool(e.get('conectado'))
        if self._prev_conectado is not None and conectado != self._prev_conectado:
            self._alarma('comunicacion', t, not conectado, e.get('error') or ('restablecida' if conectado else ''))
        self._prev_conectado = conectado

    def _alarma(self, codigo, t, activa, detalle):
        if codigo in self.ids['alarma']:
            self._sql('INSERT INTO evento_alarma (alarma_id, ciclo_id, instante, activa, detalle) '
                      'VALUES (%s, %s, %s, %s, %s)', (self.ids['alarma'][codigo], self.ciclo, t, activa, detalle[:200]))

    def _bucle(self):
        siguiente = time.monotonic()
        while self.vivo:
            if not self.db:
                self._conectar()
            fin = siguiente + PERIODO
            while True:                        # eventos hasta la próxima muestra
                try:
                    ev = self.cola.get(timeout=max(0.0, fin - time.monotonic()))
                    self._evento(ev)
                    if ev[0] == 'fin':
                        return
                except queue.Empty:
                    break
            siguiente = fin
            b = self.obtener_brazo()
            if not b or not self.modo:
                continue
            t, e = ahora(), b.leer_estado()
            self._fila_csv(t, e)
            self._muestra(t, e)


def _r(v):
    return '' if v is None else round(v, 3)
