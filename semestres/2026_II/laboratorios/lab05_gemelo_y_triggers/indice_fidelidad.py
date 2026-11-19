#!/usr/bin/env python3
"""Índice de fidelidad del gemelo digital (guía 5: más del 95 % para firmar el escudo de seguridad).

Dos comparaciones, de menos a más exigente:

  --ensayo CSV    simula el modelo de estado (continuo y discreto ZOH, Ts = 25 ms) con las mismas entradas de un
                  ensayo escalón (lab04/prueba_escalon.py) y lo compara con la posición que informa el PLC.
                  Es el equivalente en Python de crear_gemelo_simulink.m. Valida el modelo dinámico, pero la
                  referencia es la cuenta de pulsos: no detecta pasos perdidos.
  --calibre CSV   compara la posición de la garra que calcula el gemelo (cinemática de web/js/cinematica.js)
                  con la medida a mano en la planta (medicion_calibre.csv). Esta es la medición independiente
                  que pide la firma del docente.

Índice de ajuste: NRMSE = 100 (1 - ||y - y_gemelo|| / ||y - media(y)||), como goodnessOfFit/compare de MATLAB.
Para el calibre se informa además el error máximo y el índice 100 (1 - e_rms / rango de trabajo).

    python3 indice_fidelidad.py --ensayo ../lab04_identificacion_y_ddl/datos/escalon_X_4000Hz_*.csv
    python3 indice_fidelidad.py --calibre medicion_calibre.csv
"""
import argparse
import csv
import glob
import json
import math
import os
import subprocess

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..', '..', '..'))
CINEMATICA = os.path.join(RAIZ, 'web', 'js', 'cinematica.js')
K_XY = 200.0          # pulsos/mm (SUPUESTO: husillo de 5 mm)
TS = 0.025


def nrmse(y, ym):
    y, ym = np.asarray(y, float), np.asarray(ym, float)
    den = np.linalg.norm(y - y.mean())
    return 100.0 * (1 - np.linalg.norm(y - ym) / den) if den > 0 else float('nan')


def leer_ensayo(ruta):
    with open(ruta, encoding='utf-8') as f:
        cab = f.readline()
        filas = list(csv.DictReader(f))
    t = np.array([float(r['t_s']) for r in filas])
    pulsos = np.array([float(r['pulsos']) for r in filas])
    fr = np.array([float(r['f_ordenada_hz']) * int(r['en_movimiento']) for r in filas])
    return cab, t, pulsos, fr


def ensayo(ruta):
    cab, t, pulsos, fr = leer_ensayo(ruta)
    sentido = np.sign(pulsos[-1] - pulsos[0]) or 1.0
    medido = pulsos / K_XY
    # continuo: integral exacta de la entrada escalonada (retenida entre lecturas)
    cont = medido[0] + np.concatenate([[0], np.cumsum(sentido * fr[:-1] * np.diff(t) / K_XY)])
    # discreto ZOH: x(k+1) = x(k) + Ts b u(k), con u muestreado cada Ts
    tk = np.arange(t[0], t[-1] + TS, TS)
    uk = sentido * fr[np.searchsorted(t, tk, side='right') - 1]
    xk = medido[0] + np.concatenate([[0], np.cumsum(TS * uk[:-1] / K_XY)])
    disc = np.interp(t, tk, xk)
    print(f'{os.path.basename(ruta)}  ({cab.strip("# ").strip()})')
    print(f'  ajuste NRMSE continuo {nrmse(medido, cont):6.2f} %   discreto (Ts = {TS * 1000:.0f} ms) '
          f'{nrmse(medido, disc):6.2f} %   error máx. {np.abs(medido - disc).max():.2f} mm')
    return nrmse(medido, disc)


def directa(poses):
    js = ("const K=require(process.argv[1]);const P=JSON.parse(process.argv[2]);"
          "console.log(JSON.stringify(P.map(p=>{const f=K.directa(p);return {valida:f.valida,r:f.r,z:f.z};})))")
    out = subprocess.run(['node', '-e', js, CINEMATICA, json.dumps(poses)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def calibre(ruta):
    with open(ruta, encoding='utf-8') as f:
        filas = list(csv.DictReader(l for l in f if not l.startswith('#')))
    poses = [{'theta': float(r['theta_deg']), 'sX': float(r['sX_mm']), 'sY': float(r['sY_mm'])} for r in filas]
    fk = directa(poses)
    print(f'{"theta":>6s} {"sX":>6s} {"sY":>6s} | {"r gemelo":>9s} {"z gemelo":>9s} | {"r medido":>9s} {"z medido":>9s} | '
          f'{"error [mm]":>10s}')
    errores, med, gem = [], [], []
    for r, p, f in zip(filas, poses, fk):
        rm, zm = r.get('r_medido_mm', '').strip(), r.get('z_medido_mm', '').strip()
        linea = f'{p["theta"]:6.1f} {p["sX"]:6.1f} {p["sY"]:6.1f} | {f["r"]:9.1f} {f["z"]:9.1f} | '
        if not f['valida']:
            print(linea + 'pose fuera del espacio de trabajo')
            continue
        if not (rm and zm):
            print(linea + f'{"sin medir":>19s} |')
            continue
        e = math.hypot(float(rm) - f['r'], float(zm) - f['z'])
        errores.append(e)
        med += [float(rm), float(zm)]
        gem += [f['r'], f['z']]
        print(linea + f'{float(rm):9.1f} {float(zm):9.1f} | {e:10.2f}')
    if not errores:
        print('\nTodavía no hay mediciones: complete r_medido_mm y z_medido_mm en', os.path.basename(ruta))
        return None
    rango = 667 - 399            # alcance radial del espacio de trabajo (laboratorio 4: r de 399 a 667 mm)
    rms = math.sqrt(sum(e * e for e in errores) / len(errores))
    print(f'\nPoses medidas: {len(errores)}   error medio {sum(errores) / len(errores):.2f} mm   '
          f'error máximo {max(errores):.2f} mm   e_rms {rms:.2f} mm')
    print(f'Índice de fidelidad 100 (1 - e_rms / {rango} mm) = {100 * (1 - rms / rango):.2f} %   '
          f'NRMSE (r y z) = {nrmse(med, gem):.2f} %   (umbral de la guía: 95 %)')
    return 100 * (1 - rms / rango)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--ensayo', nargs='+', help='CSV de prueba_escalon.py (admite comodines)')
    ap.add_argument('--calibre', help='CSV con las mediciones de la garra')
    a = ap.parse_args()
    if not (a.ensayo or a.calibre):
        ap.error('indique --ensayo o --calibre')
    if a.ensayo:
        for ruta in sorted(sum((glob.glob(p) for p in a.ensayo), [])):
            ensayo(ruta)
    if a.calibre:
        calibre(a.calibre)


if __name__ == '__main__':
    main()
