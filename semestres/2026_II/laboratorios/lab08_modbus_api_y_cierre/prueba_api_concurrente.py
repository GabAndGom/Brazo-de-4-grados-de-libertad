#!/usr/bin/env python3
"""Auditoría de endpoints de la API REST (guía 8, tarea 65): solicitudes concurrentes, tasa de éxito,
latencia y validez del JSON de cada respuesta.

    python3 prueba_api_concurrente.py --url https://IP:8443 --usuario visita --inseguro --hilos 10 --peticiones 50

La contraseña se pide por teclado (o variable API_CLAVE). Solo hace lecturas (GET).
"""
import argparse
import getpass
import json
import os
import ssl
import statistics
import threading
import time
import urllib.error
import urllib.request

RUTAS = ['/api/v1/kpi', '/api/v1/alertas/activas', '/api/v1/ciclos?limite=20', '/api/v1/ordenes?limite=20',
         '/api/v1/telemetria/planta/1?limite=500', '/api/v1/plantas']


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--url', required=True)
    ap.add_argument('--usuario', required=True)
    ap.add_argument('--hilos', type=int, default=10)
    ap.add_argument('--peticiones', type=int, default=50, help='por hilo')
    ap.add_argument('--inseguro', action='store_true', help='no verificar el certificado TLS (autofirmado)')
    a = ap.parse_args()
    ctx = ssl._create_unverified_context() if a.inseguro else None
    clave = os.environ.get('API_CLAVE') or getpass.getpass(f'Contraseña de {a.usuario}: ')
    req = urllib.request.Request(a.url.rstrip('/') + '/api/v1/token',
                                 json.dumps({'usuario': a.usuario, 'clave': clave}).encode(),
                                 {'Content-Type': 'application/json'})
    token = json.load(urllib.request.urlopen(req, context=ctx))['token']
    res, lock = [], threading.Lock()

    def trabajador(i):
        for n in range(a.peticiones):
            ruta = RUTAS[(i + n) % len(RUTAS)]
            r = urllib.request.Request(a.url.rstrip('/') + ruta, headers={'Authorization': 'Bearer ' + token})
            t0 = time.perf_counter()
            try:
                with urllib.request.urlopen(r, timeout=15, context=ctx) as resp:
                    cuerpo = json.load(resp)
                    ok = resp.status == 200 and cuerpo.get('ok') is True and 'datos' in cuerpo
                    estado = resp.status
            except urllib.error.HTTPError as ex:
                ok, estado = False, ex.code
            except (urllib.error.URLError, ValueError, TimeoutError, OSError) as ex:
                ok, estado = False, type(ex).__name__
            with lock:
                res.append((ruta.split('?')[0], ok, estado, (time.perf_counter() - t0) * 1000))

    t0 = time.time()
    hilos = [threading.Thread(target=trabajador, args=(i,)) for i in range(a.hilos)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    dur = time.time() - t0
    total, buenas = len(res), sum(r[1] for r in res)
    print(f'{a.hilos} clientes simultáneos x {a.peticiones} peticiones = {total} en {dur:.1f} s '
          f'({total / dur:.0f} peticiones/s)')
    print(f'Respuestas JSON válidas: {buenas}/{total} = {100 * buenas / total:.2f} %')
    print(f'{"ruta":34s} {"n":>5s} {"éxito":>7s} {"mediana ms":>11s} {"p95 ms":>8s}')
    for ruta in sorted({r[0] for r in res}):
        sub = [r for r in res if r[0] == ruta]
        lat = sorted(r[3] for r in sub)
        print(f'{ruta:34s} {len(sub):5d} {100 * sum(r[1] for r in sub) / len(sub):6.1f}% '
              f'{statistics.median(lat):11.1f} {lat[int(0.95 * (len(lat) - 1))]:8.1f}')
    errores = {}
    for r in res:
        if not r[1]:
            errores[r[2]] = errores.get(r[2], 0) + 1
    if errores:
        print('Errores:', errores)


if __name__ == '__main__':
    main()
