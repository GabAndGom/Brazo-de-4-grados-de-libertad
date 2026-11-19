#!/usr/bin/env python3
"""Prueba de estímulo-respuesta (escalón de frecuencia) de un eje del brazo, guía 4.

Usa la app del gemelo (debe estar abierta en esta PC, en modo Operación local o Simulación):

    python3 prueba_escalon.py --eje X --frecuencias 1000 2000 3000 4000     -> datos/escalon_X_*.csv
    python3 prueba_escalon.py --analizar datos/escalon_X_*.csv              -> tabla K, t_d y figura

Cada ensayo: lleva el eje a 0 mm, fija la frecuencia del tren (escalón de 0 a f Hz) y manda el eje al otro
extremo (170 mm), registrando cada lectura del PLC hasta que se detiene. El CSV guarda tiempo, frecuencia
ordenada, posición contada, pulsos, banderas del PLC y las entradas (finales de carrera).

Qué mide de verdad y qué no (léase antes de usar los resultados):
  * El PLC suma los pulsos del tramo al terminarlo; la posición intermedia que muestra la app es una
    interpolación con la frecuencia ordenada, NO una medición. Por eso el análisis usa solo lo que el PLC
    informa: el instante en que empieza a moverse (bandera de tren ocupado) y el instante en que termina.
  * t_d (tiempo muerto) = desde que la PC envía la orden hasta que el PLC informa movimiento: incluye la
    latencia PPI (~155 ms por lectura) y el ciclo del PLC.
  * K = velocidad media / f [mm/s por Hz]; el valor nominal es 1/200 = 0,005 (husillo de 5 mm, SUPUESTO).
    Una K menor indica pérdida de pasos solo si se compara con la posición REAL (calibre o final de carrera);
    con la cuenta de pulsos sola, K sale siempre nominal.
  * tau no se puede medir sin un sensor continuo de posición (encoder o regla lineal).
La resolución temporal es la de la lectura PPI (~0,155 s); con 170 mm a 4 kHz (8,5 s) el error es ~2 %.
"""
import argparse
import csv
import glob
import json
import os
import time
import urllib.error
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, 'datos')
CLAVE = {'X': 'sX', 'Y': 'sY'}
PPM = 200            # pulsos por mm (1000 pulsos/vuelta, husillo de 5 mm: SUPUESTO)


class App:
    def __init__(self, url):
        self.url = url.rstrip('/')

    def _pedir(self, ruta, datos=None):
        cuerpo = None if datos is None else json.dumps(datos).encode()
        req = urllib.request.Request(self.url + ruta, cuerpo, {'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.load(r)

    def estado(self):
        return self._pedir('/api/estado')

    def orden(self, nombre, **datos):
        try:
            return self._pedir('/api/orden/' + nombre, datos)
        except urllib.error.HTTPError as ex:
            raise SystemExit(f'la app rechazó "{nombre}": {json.load(ex).get("error")}')

    def mando(self):
        try:
            self._pedir('/api/mando', {'habilitado': True})
        except urllib.error.HTTPError as ex:
            raise SystemExit(f'no se pudo tomar el mando: {json.load(ex).get("error")}')

    def esperar_reposo(self, limite=90):
        t = time.time()
        time.sleep(0.4)
        while time.time() - t < limite:
            e = self.estado()
            if not e.get('en_movimiento'):
                return e
            time.sleep(0.1)
        raise SystemExit('el eje no terminó de moverse a tiempo')


def ensayo(app, eje, f, destino, carpeta):
    e = app.estado()
    pos = {'theta': e['theta_deg'], 'sX': e['sX_mm'], 'sY': e['sY_mm']}
    pos[CLAVE[eje]] = 0.0
    app.orden('velocidad', hz=4000)
    app.orden('mover', **pos)
    app.esperar_reposo()
    app.orden('velocidad', hz=f)
    pos[CLAVE[eje]] = destino
    filas = []
    t0 = time.time()
    app.orden('mover', **pos)                      # escalón: de 0 Hz (reposo) a f Hz
    quieto_desde, ultima = None, None
    while time.time() - t0 < 120:
        e = app.estado()
        t = time.time() - t0
        clave = (e.get('pulsos') or {}).get(eje), e.get('en_movimiento'), e.get('edad_s')
        if clave != ultima:                         # una fila por lectura nueva del PLC
            ent = e.get('entradas') or {}
            filas.append({'t_s': round(t, 3), 'f_ordenada_hz': f, 'posicion_mm': round(e[CLAVE[eje] + '_mm'], 3),
                          'pulsos': (e.get('pulsos') or {}).get(eje), 'en_movimiento': int(bool(e.get('en_movimiento'))),
                          'final_atras': int(bool(ent.get('I0.1' if eje == 'X' else 'I0.3'))),
                          'final_adelante': int(bool(ent.get('I0.2' if eje == 'X' else 'I0.4'))),
                          'error_plc': (e.get('plc') or {}).get('error', ''), 'edad_lectura_s': e.get('edad_s')})
            ultima = clave
        if filas and filas[-1]['en_movimiento'] == 0 and any(r['en_movimiento'] for r in filas):
            quieto_desde = quieto_desde or t
            if t - quieto_desde > 0.6:
                break
        time.sleep(0.02)
    simulado = bool(app._pedir('/api/info').get('simulado'))
    ruta = os.path.join(carpeta, f'escalon_{eje}_{f}Hz{"_SIMULADO" if simulado else ""}_{time.strftime("%Y%m%d_%H%M%S")}.csv')
    with open(ruta, 'w', newline='', encoding='utf-8') as fh:
        fh.write(f'# brazo XK-JS1-1, eje {eje}, escalón 0 -> {f} Hz, destino {destino} mm, '
                 f'{"PLC SIMULADO (no son datos de la planta)" if simulado else "planta real"}\n')
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print('  ', os.path.relpath(ruta, AQUI))
    return ruta


def leer(ruta):
    with open(ruta, encoding='utf-8') as fh:
        cab = fh.readline().strip('# \n')
        filas = list(csv.DictReader(fh))
    return cab, [{k: (float(v) if k not in ('error_plc',) and v not in ('', 'None') else v) for k, v in r.items()}
                 for r in filas]


def analizar(rutas, figura=True):
    print(f'{"archivo":44s} {"f [Hz]":>7s} {"t_d [s]":>8s} {"T mov [s]":>9s} {"d [mm]":>7s} {"v [mm/s]":>9s} '
          f'{"K [mm/s/Hz]":>12s} {"K/K_nom":>8s}')
    resultados = []
    for ruta in rutas:
        cab, f = leer(ruta)
        mov = [r for r in f if r['en_movimiento'] == 1]
        if not mov:
            print(os.path.basename(ruta), ': el eje no se movió')
            continue
        t_ini = mov[0]['t_s']
        t_fin = next((r['t_s'] for r in f if r['t_s'] > t_ini and r['en_movimiento'] == 0), f[-1]['t_s'])
        d = (f[-1]['pulsos'] - f[0]['pulsos']) / PPM
        frec = f[0]['f_ordenada_hz']
        v = d / (t_fin - t_ini)
        K = v / frec
        resultados.append((ruta, frec, t_ini, t_fin - t_ini, d, v, K, f))
        print(f'{os.path.basename(ruta)[:44]:44s} {frec:7.0f} {t_ini:8.3f} {t_fin - t_ini:9.3f} {d:7.1f} {v:9.2f} '
              f'{K:12.6f} {K / (1 / PPM):8.3f}')
    if resultados:
        tds = [r[2] for r in resultados]
        print(f'\nTiempo muerto medio t_d = {sum(tds) / len(tds):.3f} s; K media = '
              f'{sum(r[6] for r in resultados) / len(resultados):.6f} mm/s/Hz (nominal {1 / PPM:.6f}).')
        print('Modelo identificado por eje: S(s)/F(s) = K e^(-t_d s) / s   (integrador con tiempo muerto; tau no medible)')
    if figura and resultados:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7.5, 4))
        for ruta, frec, *_, f in resultados:
            ax.step([r['t_s'] for r in f], [r['pulsos'] / PPM for r in f], where='post', label=f'{frec:.0f} Hz')
        ax.set_xlabel('tiempo desde la orden [s]')
        ax.set_ylabel('posición contada por el PLC [mm]')
        ax.grid(alpha=.3)
        ax.legend(title='escalón de frecuencia')
        ax.set_title('Respuesta al escalón de frecuencia (posición informada por el PLC)', fontsize=10)
        salida = os.path.join(os.path.dirname(resultados[0][0]), 'escalon_respuesta.png')
        fig.tight_layout()
        fig.savefig(salida, dpi=150)
        print('Figura:', os.path.relpath(salida, AQUI))
    return resultados


def main():
    ap = argparse.ArgumentParser(description='Prueba escalón de un eje del brazo (guía 4)')
    ap.add_argument('--url', default='http://localhost:8050', help='dirección de la app en esta PC')
    ap.add_argument('--eje', choices=['X', 'Y'], default='X')
    ap.add_argument('--frecuencias', type=int, nargs='+', default=[1000, 2000, 3000, 4000])
    ap.add_argument('--destino', type=float, default=170.0, help='mm (recorrido completo por defecto)')
    ap.add_argument('--analizar', nargs='+', metavar='CSV', help='solo analizar archivos ya registrados')
    a = ap.parse_args()
    if a.analizar:
        analizar(sorted(sum((glob.glob(p) for p in a.analizar), [])))
        return
    app = App(a.url)
    e = app.estado()
    if not e.get('conectado'):
        raise SystemExit('la app no está conectada al PLC')
    app.mando()
    if not e.get('referenciado'):
        print('Homing...')
        app.orden('homing')
        app.esperar_reposo(120)
    os.makedirs(DATOS, exist_ok=True)
    rutas = []
    for f in a.frecuencias:
        if not 500 <= f <= 5000:
            raise SystemExit('frecuencias entre 500 y 5000 Hz (rango probado sin pérdida de pasos)')
        print(f'Ensayo {a.eje} a {f} Hz')
        rutas.append(ensayo(app, a.eje, f, a.destino, DATOS))
    app.orden('velocidad', hz=4000)
    analizar(rutas)


if __name__ == '__main__':
    main()
