#!/usr/bin/env python3
"""LQR discreto del brazo (guía 7), en simulación. Equivalente en MATLAB: lqr_brazo.m

    python3 lqr_brazo.py

1. Discretiza el modelo de estado del laboratorio 5 (G = I, H = Ts B) con Ts = 25 ms.
2. Comprueba si el LQR de los tres ejes existe con el hardware actual (X e Y comparten el tren Q0.1):
   la ecuación de Riccati no tiene solución estabilizante porque el modo sX - sY no es controlable.
3. Calcula K con el hardware propuesto (un tren por eje, H de rango 3) y, mientras tanto, el LQR de un eje
   (base, o un carro con su relé cerrado), para varias ponderaciones Q y R.
4. Simula u(k) = -K x(k) + Kr r(k) con saturación a 5 kHz y mide sobreimpulso y esfuerzo.
Nada de esto se probó en el hardware: el brazo no tiene sensor de posición para medir x(k).
"""
import os

import numpy as np
from scipy.linalg import solve_discrete_are

AQUI = os.path.dirname(os.path.abspath(__file__))
TS = 0.025
K_THETA = 190.3 * 180 / np.pi          # pulsos/rad (medido)
K_XY = 200.0                           # pulsos/mm (SUPUESTO)
bt, bxy = 1 / K_THETA, 1 / K_XY
U_MAX = 5000.0


def dlqr(G, H, Q, R):
    P = solve_discrete_are(G, H, Q, R)
    K = np.linalg.solve(R + H.T @ P @ H, H.T @ P @ G)
    return K, P


def rango(M):
    return np.linalg.matrix_rank(M)


def simular_eje(b, K, ref, n=240):
    """Un eje: x(k+1) = x(k) + Ts b u(k), u = -K x + Kr r con Kr = K (integrador: seguimiento sin error)."""
    x, xs, us = 0.0, [], []
    for _ in range(n):
        u = float(np.clip(-K * x + K * ref, -U_MAX, U_MAX))
        xs.append(x)
        us.append(u)
        x += TS * b * u
    return np.array(xs), np.array(us)


def main():
    np.set_printoptions(precision=5, suppress=True)
    G = np.eye(3)
    print('1. Modelo discreto (ZOH, Ts = 25 ms): G = I')
    H_actual = TS * np.array([[bt, 0], [0, bxy], [0, bxy]])        # K1 y K2 cerrados: un tren para X e Y
    print('   H (hardware actual, K1 y K2 cerrados) =\n', H_actual)
    Mc = np.hstack([H_actual, G @ H_actual, G @ G @ H_actual])
    print(f'   rango de [H GH G²H] = {rango(Mc)} de 3')

    print('\n2. LQR de los tres ejes con el hardware actual:')
    try:
        K, _ = dlqr(G, H_actual, np.diag([1 / np.radians(1) ** 2, 1, 1]), np.diag([1 / 2500 ** 2] * 2))
        polos = np.linalg.eigvals(G - H_actual @ K)
        print(f'   K calculada, pero polos de lazo cerrado = {np.round(polos, 4)}')
        estable = np.all(np.abs(polos) < 1 - 1e-6)
    except (np.linalg.LinAlgError, ValueError) as ex:
        print(f'   la ecuación de Riccati no tiene solución ({type(ex).__name__})')
        estable = False
    if not estable:
        print('   un polo queda en z = 1: el modo sX - sY (diferencia entre los carros) no es controlable porque')
        print('   ambos reciben el mismo tren. Ninguna K lo estabiliza: con el hardware actual no hay LQR de 3 ejes.')

    print('\n3a. LQR de los tres ejes con un tren por eje (hardware propuesto: segundo PTO o módulo de posicionamiento)')
    H3 = TS * np.diag([bt, bxy, bxy])
    Q3 = np.diag([1 / np.radians(1) ** 2, 1.0, 1.0])     # 1° en la base pesa como 1 mm en los carros
    R3 = np.diag([1 / 2500 ** 2] * 3)                    # 2,5 kHz de esfuerzo «aceptable»
    K3, _ = dlqr(G, H3, Q3, R3)
    print('   Q = diag(1/(1°)², 1/mm², 1/mm²), R = diag(1/(2500 Hz)²) ->  K [Hz por rad o por mm] =\n', K3)
    print('   polos de lazo cerrado:', np.round(np.linalg.eigvals(G - H3 @ K3), 4))

    print('\n3b. LQR de un carro (x = s [mm], u = f [Hz]) para distintas ponderaciones (Q = 1, R = 1/ρ²):')
    print(f'   {"ρ [Hz/mm]":>10s} {"K [Hz/mm]":>10s} {"polo":>7s} {"sobreimpulso 10 mm":>19s} '
          f'{"t 5 % [s]":>10s} {"u máx [Hz]":>11s}')
    filas = []
    h = TS * bxy
    for rho in (200, 500, 1000, 2000, 5000):
        K, _ = dlqr(np.eye(1), np.array([[h]]), np.eye(1), np.array([[1 / rho ** 2]]))
        k = float(K[0, 0])
        xs, us = simular_eje(bxy, k, 10.0)
        sobre = max(0.0, (xs.max() - 10) / 10 * 100)
        cerca = np.abs(xs - 10) <= 0.5
        t5 = np.argmax(cerca) * TS if cerca.any() else float('nan')
        filas.append((rho, k, xs, us))
        print(f'   {rho:10.0f} {k:10.1f} {1 - h * k:7.4f} {sobre:18.2f} % {t5:10.3f} {np.abs(us).max():11.0f}')
    print('   Con un integrador puro y realimentación de estado el lazo es de primer orden: sin sobreimpulso.')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.5, 5.5), sharex=True)
    t = np.arange(len(filas[0][2])) * TS
    for rho, k, xs, us in filas:
        a1.plot(t, xs, label=f'ρ = {rho} Hz/mm (K = {k:.0f})')
        a2.plot(t, us)
    a1.axhline(10, color='k', lw=.6)
    a1.set_ylabel('carro X [mm]')
    a1.legend(fontsize=8)
    a1.grid(alpha=.3)
    a2.set_ylabel('u(k) [Hz]')
    a2.set_xlabel('t [s]')
    a2.grid(alpha=.3)
    a1.set_title('LQR de un carro, escalón de 10 mm, saturación a 5 kHz (SIMULACIÓN)', fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(AQUI, 'lqr_respuesta_simulada.png'), dpi=150)
    print('\nFigura: lqr_respuesta_simulada.png')


if __name__ == '__main__':
    main()
