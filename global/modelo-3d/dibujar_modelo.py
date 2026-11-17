#!/usr/bin/env python3
"""Dibuja el modelo 3D (brazo_xk-js1-1.glb) en una pose, con la cinemática de web/js/cinematica.js.

    python3 global/modelo-3d/dibujar_modelo.py            -> figuras del informe de cinemática

Aplica a los nodos los mismos movimientos que la página (base, carros, biela, brazo, pinza, varilla y
mordazas) y dibuja las caras con matplotlib, sombreadas según su normal. Requiere node, numpy y matplotlib.
"""
import json
import os
import struct
import subprocess

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
GLB = os.path.join(AQUI, 'brazo_xk-js1-1.glb')
FIG = os.path.join(RAIZ, 'semestres', '2026_II', 'modelo-3d', 'informe', 'figuras')
COLOR = {0: (0.80, 0.82, 0.85), 1: (0.55, 0.58, 0.63), 2: (0.15, 0.15, 0.16), 3: (0.76, 0.38, 0.05),
         4: (0.85, 0.72, 0.30), 5: (0.2, 0.2, 0.22)}


def leer_glb(ruta):
    b = open(ruta, 'rb').read()
    lj = struct.unpack('<I', b[12:16])[0]
    g = json.loads(b[20:20 + lj])
    binario = b[20 + lj + 8:]
    def acc(i):
        a = g['accessors'][i]; v = g['bufferViews'][a['bufferView']]
        return np.frombuffer(binario, '<f4', a['count'] * 3, v.get('byteOffset', 0)).reshape(-1, 3)
    nodos = []
    for n in g['nodes']:
        prims = []
        if 'mesh' in n:
            for p in g['meshes'][n['mesh']]['primitives']:
                prims.append((acc(p['attributes']['POSITION']).reshape(-1, 3, 3), p.get('material', 0)))
        nodos.append(dict(nombre=n['name'], t=np.array(n.get('translation', [0, 0, 0])), hijos=n.get('children', []),
                          prims=prims))
    return nodos


def pose(q):
    js = ("const K=require(process.argv[1]);const f=K.directa(JSON.parse(process.argv[2]));"
          "console.log(JSON.stringify({phi:f.phi,gamma:f.gamma,biela:f.angBiela,varilla:f.angVarilla,"
          "g:f.posBloque1,r:f.r,z:f.z}))")
    out = subprocess.run(['node', '-e', js, os.path.join(RAIZ, 'web', 'js', 'cinematica.js'), json.dumps(q)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def rz(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def ry(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def triangulos(nodos, q, garra_cerrada):
    f = pose(q)
    R = np.radians
    mov = {  # (rotación, traslación extra en x) de cada nodo, como en web/js/modelo3d.js
        'base_giratoria': (ry(R(q['theta'])), 0), 'carro_x': (np.eye(3), q['sX'] / 1000),
        'carro_y': (np.eye(3), f['g'] / 1000), 'biela_12': (rz(R(f['biela'])), 0), 'brazo_9': (rz(R(f['phi'])), 0),
        'pinza': (rz(R(f['gamma'] - f['phi'])), 0), 'varilla_13': (rz(R(f['varilla'])), 0),
        'mordaza_der': (ry(R(0 if garra_cerrada else -25)), 0), 'mordaza_izq': (ry(R(0 if garra_cerrada else 25)), 0)}
    salida = []
    def recorrer(i, Rp, tp):
        n = nodos[i]
        Rl, dx = mov.get(n['nombre'], (np.eye(3), 0))
        t = tp + Rp @ (n['t'] + [dx, 0, 0])
        Rw = Rp @ Rl
        for tri, mat in n['prims']:
            salida.append(((tri.reshape(-1, 3) @ Rw.T + t).reshape(-1, 3, 3), mat))
        for h in n['hijos']:
            recorrer(h, Rw, t)
    recorrer(0, np.eye(3), np.zeros(3))
    return salida, f


def dibujar(q, nombre, vista, garra_cerrada=False, mesa=True, zoom=None, titulo=None):
    nodos = leer_glb(GLB)
    tris, f = triangulos(nodos, q, garra_cerrada)
    fig = plt.figure(figsize=(7, 5.2))
    ax = fig.add_subplot(111, projection='3d')
    luz = np.array([0.35, -0.5, 0.8]); luz /= np.linalg.norm(luz)
    todos = []
    for tri, mat in tris:
        p = tri[:, :, [0, 2, 1]] * [1, -1, 1] * 1000          # glTF (x, y arriba, z) -> (X, Y = -z, Z arriba) en mm
        n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
        n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
        k = 0.45 + 0.55 * np.abs(n @ luz)
        col = np.clip(np.array(COLOR.get(mat, (0.8, 0.8, 0.8)))[None, :] * k[:, None], 0, 1)
        todos.append(p)
        ax.add_collection3d(Poly3DCollection(p, facecolors=col, edgecolors=col * 0.92, linewidths=0.05))
    if mesa:
        X, Y = np.meshgrid([-450, 450], [-320, 320])
        ax.plot_surface(X + 250, Y, np.zeros_like(X), color=(0.62, 0.66, 0.72), alpha=0.25, zorder=-1)
    ax.set_proj_type('ortho')
    pts = np.concatenate([p.reshape(-1, 3) for p in todos])
    c = (pts.max(0) + pts.min(0)) / 2
    m = (pts.max(0) - pts.min(0)).max() / 2 * (zoom or 0.72)   # matplotlib deja mucho margen en 3D
    if zoom:
        c = np.array([f['r'] - 40, 0, f['z']])
    ax.set_xlim(c[0] - m, c[0] + m); ax.set_ylim(c[1] - m, c[1] + m); ax.set_zlim(c[2] - m, c[2] + m)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(*vista)
    ax.set_axis_off()
    if titulo:
        ax.set_title(titulo, fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, nombre), dpi=150, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    print(nombre)


if __name__ == '__main__':
    os.makedirs(FIG, exist_ok=True)
    dibujar({'theta': 25, 'sX': 80, 'sY': 50}, 'modelo_3d_isometrica.png', (22, -60))
    dibujar({'theta': 0, 'sX': 80, 'sY': 50}, 'modelo_3d_lateral.png', (0, -90))
    dibujar({'theta': 0, 'sX': 40, 'sY': 40}, 'modelo_3d_superior.png', (90, -90))
    dibujar({'theta': 0, 'sX': 0, 'sY': 45}, 'modelo_3d_pose_manual.png', (0, -90))
    dibujar({'theta': 0, 'sX': 80, 'sY': 50}, 'garra_abierta.png', (55, -120), garra_cerrada=False, mesa=False, zoom=0.22)
    dibujar({'theta': 0, 'sX': 80, 'sY': 50}, 'garra_cerrada.png', (55, -120), garra_cerrada=True, mesa=False, zoom=0.22)
