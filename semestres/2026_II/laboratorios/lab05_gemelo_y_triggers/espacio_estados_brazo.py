#!/usr/bin/env python3
"""Modelo en espacio de estados del brazo XK-JS1-1 (guías 4 y 5).

    python3 espacio_estados_brazo.py

Modelo analítico de los tres ejes movidos por motores paso a paso en lazo abierto. Mientras el motor no
pierde pasos, cada pulso avanza el eje una cantidad fija, así que la posición es la integral de la
frecuencia de pulsos:

    estado  x = [theta (rad), sX (mm), sY (mm)]
    entrada u = [f0 (Hz, PTO0 -> base), f1 (Hz, PTO1 compartido -> X/Y por K1/K2)]   (con signo = DIR)
    dx/dt = A x + B(sigma) u,  A = 0,  B(sigma) = [[b_t, 0], [0, k1*b_xy], [0, k2*b_xy]]
    salida  y = C x,  C = J(q0) (jacobiano de la cinemática: posición cartesiana de la garra, linealizada)

sigma = (k1, k2) es el estado de los relés K1 (Q0.5) y K2 (Q0.6): el sistema es conmutado.

Constantes (manual técnico, cap. 4 y 13):
    base: 190,3 pulsos/° medidos con transportador (26/10/2026)
    carros: 1000 pulsos/vuelta / 5 mm por vuelta del husillo = 200 pulsos/mm  (paso de 5 mm: SUPUESTO)
    J(q0) en el centro (0°, 85 mm, 85 mm): K.jacobiano() de web/js/cinematica.js con las cotas del modelo de
    Inventor (17/11/2026), theta en rad

Calcula: rango de controlabilidad y observabilidad por modo de los relés, modelo discreto con
retención de orden cero (ZOH) y funciones de transferencia por eje. Equivalente en MATLAB:
espacio_estados_brazo.m
"""
import numpy as np
from scipy.signal import cont2discrete

K_THETA = 190.3 * 180 / np.pi          # pulsos/rad
K_XY = 1000 / 5                        # pulsos/mm (SUPUESTO: husillo de 5 mm)
b_t, b_xy = 1 / K_THETA, 1 / K_XY

A = np.zeros((3, 3))
C_centro = np.array([[0.0, 1.0, -0.397],      # X  = d(X, Y, Z)/d(theta, sX, sY) en (0°, 85, 85)
                     [574.8, 0.0, 0.0],       # Y
                     [0.0, 0.0, 2.622]])      # Z
C_estimado = np.eye(3)                         # el gemelo "mide" los tres estados contando pulsos


def B(k1, k2):
    return np.array([[b_t, 0.0], [0.0, k1 * b_xy], [0.0, k2 * b_xy]])


def ctrb(A, B):
    n = A.shape[0]
    return np.hstack([np.linalg.matrix_power(A, i) @ B for i in range(n)])


def obsv(A, C):
    n = A.shape[0]
    return np.vstack([C @ np.linalg.matrix_power(A, i) for i in range(n)])


def main():
    np.set_printoptions(precision=6, suppress=True)
    print(f'b_theta = {b_t:.4e} rad/pulso   b_xy = {b_xy:.4e} mm/pulso\n')
    modos = {'K1 (X)': (1, 0), 'K2 (Y)': (0, 1), 'K1 y K2 (X e Y a la vez)': (1, 1), 'ninguno': (0, 0)}
    print('Controlabilidad por modo de los relés (n = 3):')
    for nombre, s in modos.items():
        r = np.linalg.matrix_rank(ctrb(A, B(*s)))
        print(f'  {nombre:26s} rango Mc = {r}  -> {"controlable" if r == 3 else "NO controlable"}')
    union = np.hstack([B(1, 0), B(0, 1)])
    print(f'  conmutando K1 <-> K2      rango [B(K1) B(K2)] = {np.linalg.matrix_rank(union)}'
          ' -> alcanzable por conmutación')
    print('\nObservabilidad:')
    print(f'  C = J(centro)            rango Mo = {np.linalg.matrix_rank(obsv(A, C_centro))}')
    print(f'  C = I (cuenta de pulsos) rango Mo = {np.linalg.matrix_rank(obsv(A, C_estimado))}')
    print('  sensores reales (finales e inductivo): salidas binarias, no hay C lineal -> no observable en continuo')

    print('\nModelo discreto con ZOH (modo K1 y K2):')
    for ts in (0.025, 0.155):
        G, H, *_ = cont2discrete((A, B(1, 1), C_estimado, np.zeros((3, 2))), ts, method='zoh')
        print(f'  Ts = {ts*1000:.0f} ms: G =\n{G}\n  H =\n{H}')
    print('\nFunciones de transferencia por eje (entrada: frecuencia en Hz):')
    print(f'  base:  Theta(s)/F0(s) = {b_t:.4e} / s        G(z) = {b_t:.4e} Ts / (z - 1)')
    print(f'  carro: S(s)/F1(s)     = {b_xy:.4e} / s        G(z) = {b_xy:.4e} Ts / (z - 1)')


if __name__ == '__main__':
    main()
