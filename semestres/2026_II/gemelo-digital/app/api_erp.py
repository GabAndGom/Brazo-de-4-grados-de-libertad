"""API REST del ERP (laboratorio 8) y datos del dashboard (laboratorio 7), sobre la base brazo4gdl.

Rutas (todas GET, JSON; con ?formato=csv la telemetría se descarga como CSV):

    /api/v1/plantas                         plantas registradas y si están en operación
    /api/v1/telemetria/planta/{id}          serie de tiempo: ?tag=ZI-102&desde=...&hasta=...&cada=60&limite=5000
    /api/v1/alertas/activas                 alarmas cuyo último evento está activo
    /api/v1/alertas                         historial: ?desde=...&limite=200
    /api/v1/ciclos                          ciclos de operación (vista v_ciclo)
    /api/v1/ordenes                         últimas órdenes con su resultado
    /api/v1/kpi                             indicadores del dashboard, con la eficiencia homeostática
    /api/v1/sesiones                        historial de ingresos (solo operador)

El acceso lo controla gemelo_brazo.py: sesión de la app (cookie) o «Authorization: Bearer <token>»
obtenido con POST /api/v1/token. Esta capa solo lee: ninguna ruta modifica la base, salvo
rearmar() (operador), que vuelve a poner la planta en operación después de un disparo del trigger.
"""
import csv
import io
import threading
from datetime import datetime, timedelta, timezone

import telemetria

psycopg = telemetria.psycopg
SEVERIDAD_MINIMA = 2          # alarmas que cuentan para la eficiencia homeostática: falla (2) y crítica (3)


class ErrorAPI(Exception):
    def __init__(self, codigo, texto):
        super().__init__(texto)
        self.codigo = codigo


def _fecha(texto, defecto):
    if not texto:
        return defecto
    try:
        t = datetime.fromisoformat(texto.replace('Z', '+00:00'))
    except ValueError:
        raise ErrorAPI(400, f'fecha no válida: {texto} (use ISO 8601, p. ej. 2026-11-18T10:00:00-04:00)')
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def _entero(texto, defecto, minimo, maximo):
    try:
        return max(minimo, min(maximo, int(texto))) if texto else defecto
    except ValueError:
        raise ErrorAPI(400, f'número no válido: {texto}')


def _json(v):
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, timedelta):
        return round(v.total_seconds(), 1)
    return v


def _filas(cur):
    nombres = [d.name for d in cur.description]
    return [{n: _json(v) for n, v in zip(nombres, fila)} for fila in cur.fetchall()]


class ERP:
    def __init__(self):
        self.db = None
        self.lock = threading.Lock()

    def _cur(self):
        if psycopg is None:
            raise ErrorAPI(503, 'la PC no tiene psycopg: pip install "psycopg[binary]"')
        if self.db is None or self.db.closed:
            try:
                self.db = psycopg.connect(telemetria.conninfo(), autocommit=True, connect_timeout=3)
            except psycopg.Error as ex:
                raise ErrorAPI(503, 'sin base de datos: ' + str(ex).strip().splitlines()[0])
        return self.db.cursor()

    def _consulta(self, sql, parametros=()):
        with self.lock:
            try:
                cur = self._cur()
                cur.execute(sql, parametros)
                return cur
            except psycopg.OperationalError as ex:
                self.db = None
                raise ErrorAPI(503, 'se perdió la base de datos: ' + str(ex).strip().splitlines()[0])

    # ------------------------------------------------------------------ rutas
    def atender(self, ruta, q, rol):
        """Devuelve (código, cuerpo, tipo) para una ruta /api/v1/..."""
        p = ruta[len('/api/v1/'):].strip('/').split('/')
        g = lambda k: (q.get(k) or [None])[0]
        if p == ['plantas']:
            return self._ok(self.plantas())
        if len(p) == 3 and p[:2] == ['telemetria', 'planta']:
            filas = self.telemetria(p[2], g('tag'), g('desde'), g('hasta'), g('cada'), g('limite'))
            if g('formato') == 'csv':
                return 200, _csv(filas), 'text/csv; charset=utf-8'
            return self._ok(filas)
        if p == ['alertas', 'activas']:
            return self._ok(self.alertas_activas())
        if p == ['alertas']:
            return self._ok(self.alertas(g('desde'), g('limite')))
        if p == ['ciclos']:
            return self._ok(self.ciclos(g('limite')))
        if p == ['ordenes']:
            return self._ok(self.ordenes(g('limite')))
        if p == ['kpi']:
            return self._ok(self.kpi(g('dias')))
        if p == ['sesiones']:
            if rol != 'operador':
                raise ErrorAPI(403, 'solo un operador puede ver el historial de sesiones')
            return self._ok(self.sesiones(g('limite')))
        raise ErrorAPI(404, 'ruta desconocida')

    @staticmethod
    def _ok(datos):
        return 200, {'ok': True, 'datos': datos}, 'json'

    def plantas(self):
        return _filas(self._consulta('SELECT id, nombre, tipo, plc, en_operacion FROM sistema ORDER BY id'))

    def telemetria(self, planta, tag, desde, hasta, cada, limite):
        try:
            planta = int(planta)
        except ValueError:
            raise ErrorAPI(400, 'el id de la planta debe ser un número')
        fin = _fecha(hasta, datetime.now(timezone.utc))
        ini = _fecha(desde, fin - timedelta(hours=1))
        limite = _entero(limite, 5000, 1, 100000)
        cada = _entero(cada, 0, 0, 86400)
        filtro, parametros = '', [planta, ini, fin]
        if tag:
            filtro = ' AND v.tag_isa = %s'
            parametros.append(tag)
        if cada:            # promedio por intervalo (para gráficos largos)
            sql = ('SELECT v.tag_isa AS tag, v.unidad, to_timestamp(floor(extract(epoch FROM m.instante) / %s) * %s) '
                   'AS instante, avg(m.valor) AS valor, count(*) AS n '
                   'FROM muestra m JOIN variable v ON v.id = m.variable_id JOIN eje e ON e.id = v.eje_id '
                   'WHERE e.sistema_id = %s AND m.instante BETWEEN %s AND %s' + filtro +
                   ' GROUP BY 1, 2, 3 ORDER BY 3, 1 LIMIT %s')
            parametros = [cada, cada] + parametros
        else:
            sql = ('SELECT v.tag_isa AS tag, v.unidad, m.instante, m.valor, m.ciclo_id '
                   'FROM muestra m JOIN variable v ON v.id = m.variable_id JOIN eje e ON e.id = v.eje_id '
                   'WHERE e.sistema_id = %s AND m.instante BETWEEN %s AND %s' + filtro +
                   ' ORDER BY m.instante, v.tag_isa LIMIT %s')
        return _filas(self._consulta(sql, parametros + [limite]))

    def alertas_activas(self):
        return _filas(self._consulta(
            'SELECT a.codigo, a.severidad, a.descripcion, ult.instante, ult.detalle, ult.ciclo_id '
            'FROM (SELECT DISTINCT ON (alarma_id) alarma_id, activa, instante, detalle, ciclo_id '
            '      FROM evento_alarma ORDER BY alarma_id, instante DESC) ult '
            'JOIN alarma a ON a.id = ult.alarma_id WHERE ult.activa ORDER BY a.severidad DESC, ult.instante'))

    def alertas(self, desde, limite):
        ini = _fecha(desde, datetime.now(timezone.utc) - timedelta(days=7))
        return _filas(self._consulta(
            'SELECT e.instante, a.codigo, a.severidad, e.activa, e.detalle, e.ciclo_id '
            'FROM evento_alarma e JOIN alarma a ON a.id = e.alarma_id WHERE e.instante >= %s '
            'ORDER BY e.instante DESC LIMIT %s', (ini, _entero(limite, 200, 1, 5000))))

    def ciclos(self, limite):
        return _filas(self._consulta('SELECT * FROM v_ciclo ORDER BY inicio DESC LIMIT %s',
                                     (_entero(limite, 50, 1, 1000),)))

    def ordenes(self, limite):
        return _filas(self._consulta(
            'SELECT o.instante, o.tipo, o.aceptada, o.motivo, coalesce(u.nombre, %s) AS usuario, o.ciclo_id '
            'FROM orden o LEFT JOIN usuario u ON u.id = o.usuario_id ORDER BY o.instante DESC LIMIT %s',
            ('PC local / usuario de la app', _entero(limite, 50, 1, 1000))))

    def sesiones(self, limite):
        return _filas(self._consulta(
            'SELECT instante, nombre_usado AS usuario, host(ip) AS ip, exito FROM sesion '
            'ORDER BY instante DESC LIMIT %s', (_entero(limite, 50, 1, 1000),)))

    def kpi(self, dias):
        dias = _entero(dias, 7, 1, 365)
        ini = datetime.now(timezone.utc) - timedelta(days=dias)
        c = self._consulta(
            "SELECT count(*), coalesce(sum(extract(epoch FROM (coalesce(fin, now()) - greatest(inicio, %s)))), 0) "
            "FROM ciclo_operacion WHERE coalesce(fin, now()) > %s", (ini, ini)).fetchone()
        ciclos, t_operacion = c[0], float(c[1])
        o = self._consulta('SELECT count(*), count(*) FILTER (WHERE aceptada) FROM orden WHERE instante > %s',
                           (ini,)).fetchone()
        muestras = self._consulta('SELECT count(*) FROM muestra WHERE instante > %s', (ini,)).fetchone()[0]
        t_alarma = self._tiempo_con_alarma(ini)
        eficiencia = None if t_operacion <= 0 else max(0.0, 1 - t_alarma / t_operacion)
        planta = self._consulta('SELECT en_operacion FROM sistema ORDER BY id LIMIT 1').fetchone()
        posicion = _filas(self._consulta('SELECT tag_isa, unidad, valor, instante FROM v_ultima_posicion'))
        return {'dias': dias, 'ciclos': ciclos, 'horas_operacion': round(t_operacion / 3600, 3),
                'horas_con_alarma': round(t_alarma / 3600, 3),
                'eficiencia_homeostatica': None if eficiencia is None else round(eficiencia, 4),
                'formula': 'eta_H = 1 - (tiempo con alarma de severidad >= 2 activa) / (tiempo en operación)',
                'ordenes': o[0], 'ordenes_aceptadas': o[1],
                'porcentaje_aceptadas': round(o[1] / o[0], 4) if o[0] else None,
                'muestras': muestras, 'alarmas_activas': len(self.alertas_activas()),
                'planta_en_operacion': bool(planta[0]) if planta else None, 'ultima_posicion': posicion}

    def _tiempo_con_alarma(self, ini):
        """Segundos (desde ini) con al menos una alarma de severidad >= 2 activa, sin contar dos veces los solapes.
        Cada alarma está activa desde un evento activa = true hasta su siguiente evento o el fin del ciclo."""
        filas = self._consulta(
            'SELECT inicio, fin FROM ('
            '  SELECT e.instante AS inicio, e.activa, '
            '         least(coalesce(lead(e.instante) OVER (PARTITION BY e.alarma_id, e.ciclo_id ORDER BY e.instante), '
            '                        c.fin, now()), coalesce(c.fin, now())) AS fin '
            '  FROM evento_alarma e JOIN alarma a ON a.id = e.alarma_id JOIN ciclo_operacion c ON c.id = e.ciclo_id '
            '  WHERE a.severidad >= %s) t '
            'WHERE activa AND fin > %s ORDER BY inicio', (SEVERIDAD_MINIMA, ini)).fetchall()
        total, fin_union = 0.0, None
        for a, b in filas:
            a = max(a, ini)
            if fin_union is None or a > fin_union:
                total += (b - a).total_seconds()
                fin_union = b
            elif b > fin_union:
                total += (b - fin_union).total_seconds()
                fin_union = b
        return max(0.0, total)

    def rearmar(self, planta=1):
        cur = self._consulta('UPDATE sistema SET en_operacion = true WHERE id = %s RETURNING nombre', (planta,))
        fila = cur.fetchone()
        if not fila:
            raise ErrorAPI(404, 'no existe esa planta')
        return {'ok': True, 'planta': fila[0], 'en_operacion': True}


def _csv(filas):
    salida = io.StringIO()
    if filas:
        w = csv.DictWriter(salida, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    return salida.getvalue()
