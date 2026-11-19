#!/usr/bin/env python3
"""Certificado de seguridad RBAC (guía 7, entregable 57 y tarea 52 del auxiliar).

Ataca el acceso por red de la app con tokens inválidos, roles sin permiso y peticiones de otro origen, y
deja el resultado de cada prueba en certificado_rbac_<fecha>.md. Las contraseñas se piden por teclado
(o variables RBAC_CLAVE_OPERADOR y RBAC_CLAVE_OBSERVADOR); nunca se guardan.

    python3 prueba_rbac.py --url https://IP-DE-LA-PC:8443 --operador ana --observador visita

Con el certificado autofirmado del laboratorio use --inseguro (no verifica el certificado TLS).
Prueba la app en modo simulación para no mover el brazo: ninguna orden de las pruebas debería aceptarse,
pero si alguna lo fuera, el brazo se movería.
"""
import argparse
import getpass
import json
import os
import secrets
import ssl
import time
import urllib.error
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))


class Cliente:
    def __init__(self, url, inseguro):
        self.url = url.rstrip('/')
        self.ctx = ssl._create_unverified_context() if inseguro else None

    def pedir(self, metodo, ruta, datos=None, token=None, cabeceras=None):
        h = {'Content-Type': 'application/json'}
        if token:
            h['Authorization'] = 'Bearer ' + token
        h.update(cabeceras or {})
        cuerpo = None if datos is None else json.dumps(datos).encode()
        req = urllib.request.Request(self.url + ruta, cuerpo, h, method=metodo)
        try:
            with urllib.request.urlopen(req, timeout=8, context=self.ctx) as r:
                return r.status, r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as ex:
            return ex.code, ex.read().decode('utf-8', 'replace')

    def token(self, usuario, clave):
        c, cuerpo = self.pedir('POST', '/api/v1/token', {'usuario': usuario, 'clave': clave})
        if c != 200:
            raise SystemExit(f'no se pudo ingresar como {usuario}: {cuerpo}')
        return json.loads(cuerpo)['token']


def main():
    ap = argparse.ArgumentParser(description='Pruebas de seguridad RBAC del acceso por red')
    ap.add_argument('--url', required=True)
    ap.add_argument('--operador', required=True, help='usuario con rol operador')
    ap.add_argument('--observador', required=True, help='usuario con rol observador')
    ap.add_argument('--inseguro', action='store_true', help='no verificar el certificado TLS (autofirmado)')
    a = ap.parse_args()
    clave_op = os.environ.get('RBAC_CLAVE_OPERADOR') or getpass.getpass(f'Contraseña de {a.operador}: ')
    clave_ob = os.environ.get('RBAC_CLAVE_OBSERVADOR') or getpass.getpass(f'Contraseña de {a.observador}: ')
    c = Cliente(a.url, a.inseguro)
    t_op, t_ob = c.token(a.operador, clave_op), c.token(a.observador, clave_ob)
    falso = secrets.token_urlsafe(32)
    mover = {'theta': 0, 'sX': 10, 'sY': 10}
    pruebas = [
        ('API sin token', 'GET', '/api/v1/kpi', None, None, None, 401),
        ('Token inventado (32 bytes aleatorios)', 'GET', '/api/v1/alertas/activas', None, falso, None, 401),
        ('Token vacío en la cabecera', 'GET', '/api/v1/kpi', None, None, {'Authorization': 'Bearer '}, 401),
        ('Token del observador alterado en 1 carácter', 'GET', '/api/v1/kpi', None,
         t_ob[:-1] + ('A' if t_ob[-1] != 'A' else 'B'), None, 401),
        ('Estado en vivo sin token', 'GET', '/api/estado', None, None, None, 401),
        ('Orden de movimiento sin token', 'POST', '/api/orden/mover', mover, None, None, 401),
        ('Orden de movimiento con token inventado', 'POST', '/api/orden/mover', mover, falso, None, 401),
        ('Observador: orden de movimiento', 'POST', '/api/orden/mover', mover, t_ob, None, 403),
        ('Observador: orden de garra', 'POST', '/api/orden/garra', {'cerrada': True}, t_ob, None, 403),
        ('Observador: tomar el mando', 'POST', '/api/mando', {'habilitado': True}, t_ob, None, 403),
        ('Observador: rearmar la planta en la base', 'POST', '/api/v1/planta/rearmar', {}, t_ob, None, 403),
        ('Observador: historial de sesiones', 'GET', '/api/v1/sesiones', None, t_ob, None, 403),
        ('Observador: lectura de telemetría (permitida)', 'GET', '/api/v1/telemetria/planta/1?limite=5', None, t_ob,
         None, 200),
        ('Observador: KPI (permitido)', 'GET', '/api/v1/kpi', None, t_ob, None, 200),
        ('Operador: historial de sesiones (permitido)', 'GET', '/api/v1/sesiones?limite=5', None, t_op, None, 200),
        ('Menú de administración desde la red', 'GET', '/api/app', None, t_op, None, 403),
        ('Cambio de modo desde la red', 'POST', '/api/app/modo', {'modo': 'simulacion'}, t_op, None, 403),
        ('Clave incorrecta al pedir token', 'POST', '/api/v1/token', {'usuario': a.operador, 'clave': 'incorrecta'},
         None, None, 401),
    ]
    filas, aprobadas = [], 0
    for nombre, metodo, ruta, datos, token, cab, esperado in pruebas:
        codigo, cuerpo = c.pedir(metodo, ruta, datos, token, cab)
        ok = codigo == esperado
        aprobadas += ok
        try:
            msg = json.loads(cuerpo).get('error', 'correcto')
        except ValueError:
            msg = cuerpo[:60]
        filas.append((nombre, f'{metodo} {ruta.split("?")[0]}', esperado, codigo, 'APROBADA' if ok else 'FALLA', msg))
        print(f'{"OK " if ok else "MAL"} {codigo} (esperado {esperado})  {nombre}')
    fecha = time.strftime('%Y-%m-%d %H:%M')
    ruta = os.path.join(AQUI, time.strftime('certificado_rbac_%Y%m%d_%H%M.md'))
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(f'# Certificado de seguridad RBAC · brazo XK-JS1-1\n\n'
                f'- Fecha: {fecha}\n- Servidor: `{a.url}`\n- Usuarios de prueba: operador `{a.operador}`, '
                f'observador `{a.observador}`\n- Resultado: **{aprobadas} de {len(pruebas)} pruebas aprobadas**\n\n'
                '| Prueba | Petición | Esperado | Obtenido | Resultado | Respuesta del servidor |\n'
                '|---|---|---|---|---|---|\n')
        for fila in filas:
            f.write('| ' + ' | '.join(str(x).replace('|', '/') for x in fila) + ' |\n')
        f.write('\n401 = sin sesión válida; 403 = sesión válida sin permiso para esa acción.\n\n'
                'Ejecutó: ____________________ (auxiliar)    Revisó: ____________________ (docente)\n')
    print(f'\n{aprobadas} de {len(pruebas)} aprobadas. Certificado: {os.path.basename(ruta)}')


if __name__ == '__main__':
    main()
