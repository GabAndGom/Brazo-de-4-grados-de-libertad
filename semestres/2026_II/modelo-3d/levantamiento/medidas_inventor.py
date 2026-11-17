#!/usr/bin/env python3
"""Extrae las cotas del brazo del modelo de Inventor del equipo (exportado a STL).

    python3 medidas_inventor.py [carpeta con ensambleGeneral_1_*.stl]   -> medidas_inventor.json

Por defecto lee global/modelo-3d/inventor/stl/ del repositorio.

En Inventor: abrir ensambleGeneral.iam, Archivo > Exportar > Formato CAD > STL, opción
"un archivo por instancia de pieza" (cada pieza queda en su posición dentro del ensamble), unidades mm.

1. Lleva el ensamble a un sistema propio: z = normal del disco de la base, x = dirección de las guías,
   origen en el centro del disco, sobre su cara inferior.
2. Mide cajas de las piezas y busca los pasadores (A, B, C, E, A', E') ajustando circunferencias a las
   caras cilíndricas de los agujeros.
3. Escribe las cotas con los nombres de web/js/cinematica.js y los puntos en el plano del brazo
   (u hacia adelante desde el eje de giro, h desde el eje del carro X).
Solo usa numpy.
"""
import collections, glob, json, math, os, struct, sys
import numpy as np


def leer_stl(f):
    b = open(f, 'rb').read()
    if b[:5] == b'solid' and b'facet' in b[:300]:
        v = [list(map(float, l.split()[1:4])) for l in b.decode().splitlines() if l.strip().startswith('vertex')]
        return np.array(v).reshape(-1, 3, 3)
    n = struct.unpack('<I', b[80:84])[0]
    d = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    return d['v'].reshape(-1, 3, 3).astype(float)


def circunferencia(p):
    A = np.c_[2 * p[:, 0], 2 * p[:, 1], np.ones(len(p))]
    c, *_ = np.linalg.lstsq(A, (p ** 2).sum(1), rcond=None)
    r = math.sqrt(c[2] + c[0] ** 2 + c[1] ** 2)
    return c[0], c[1], r, np.abs(np.hypot(p[:, 0] - c[0], p[:, 1] - c[1]) - r).max()


def pasadores(t, eje=1, rmax=12):
    """Centros de los agujeros o ejes cilíndricos paralelos a 'eje' (en el plano de los otros dos)."""
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    sel = np.where(np.abs(n[:, eje]) < 0.05)[0]
    vmap = collections.defaultdict(list)
    for i in sel:
        for v in t[i]:
            vmap[tuple(np.round(v, 3))].append(i)
    par = {i: i for i in sel}

    def raiz(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for lst in vmap.values():
        for j in lst[1:]:
            par[raiz(j)] = raiz(lst[0])
    grupos = collections.defaultdict(list)
    for i in sel:
        grupos[raiz(i)].append(i)
    otros = [k for k in (0, 1, 2) if k != eje]
    out = []
    for g in grupos.values():
        if len(g) < 6:
            continue
        p = t[g].reshape(-1, 3)
        cx, cz, r, res = circunferencia(p[:, otros])
        if r < rmax and res < 0.3:
            out.append(np.array([cx, cz]))
    return sorted(out, key=lambda c: (c[0], c[1]))


def main(carpeta):
    P = {os.path.basename(f)[len('ensambleGeneral_1_'):-4]: leer_stl(f)
         for f in sorted(glob.glob(os.path.join(carpeta, 'ensambleGeneral_1_*.stl')))}
    # sistema propio
    t = P['baseBrazo_14']
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    up = n[np.argmax(np.linalg.norm(n, axis=1))]
    up /= np.linalg.norm(up)
    resto = np.vstack([v.reshape(-1, 3) for k, v in P.items() if k != 'baseBrazo_14']).mean(0)
    if (resto - t.reshape(-1, 3).mean(0)) @ up < 0:
        up = -up
    v = P['barraDesliz_3'].reshape(-1, 3)
    v = v - v.mean(0)
    d = np.linalg.eigh(v.T @ v)[1][:, -1]
    fx = d - (d @ up) * up
    fx /= np.linalg.norm(fx)
    R = np.vstack([fx, np.cross(up, fx), up])
    vd = t.reshape(-1, 3) @ R.T
    o = np.array([(vd[:, 0].min() + vd[:, 0].max()) / 2, (vd[:, 1].min() + vd[:, 1].max()) / 2, vd[:, 2].min()])
    L = {k: (v.reshape(-1, 3) @ R.T - o).reshape(-1, 3, 3) for k, v in P.items()}
    # el frente (garra) queda hacia -x; si no, se invierte
    if L['pinza_15'][..., 0].mean() > 0:
        R[0], R[1] = -R[0], -R[1]
        L = {k: (v.reshape(-1, 3) @ R.T - (o * [-1, -1, 1])).reshape(-1, 3, 3) for k, v in P.items()}

    def caja(k):
        v = L[k].reshape(-1, 3)
        return v.min(0), v.max(0)
    A = pasadores(L['Pieza14_10'])[0]
    E = pasadores(L['trasePinza_18'])[0]
    C = pasadores(L['soporteBarrasBrazo_9'])[0]
    B = pasadores(L['soporteBarrasBrazo_20'])[0]
    E2, A2 = pasadores(L['barillaBrazo_23'])[:2]
    lo2, hi2 = caja('BaseRodilloY_8')          # bloque 2 (fijo a la columna)
    lo1, hi1 = caja('BaseRodilloY_7')          # bloque 1 (carro Y)
    lop, hip = caja('soporteCorrederas_2')     # placa delantera
    _, hip2 = caja('soporteCorrederas_1')      # placa trasera
    loe, hie = caja('soporteBarrasBrazo_9')    # escuadra 6
    lob, hib = caja('baseBrazo_14')
    loc, hic = caja('baseCorredera_11')
    lsp, hsp = caja('soportePinza_17')
    # mordazas: pinza_16 es pinza_15 espejada y abierta ~47°; el TCP se toma con la garra cerrada:
    # centro de la mordaza 15 a lo largo de la pinza y en altura, en el plano medio del cuerpo
    lj, hj = caja('pinza_15')
    guias = [caja(f'barraDesliz_{i}') for i in (3, 4, 5, 6)]
    h0 = (lo2[2] + hi2[2]) / 2                 # eje del carro X (centro del bloque 2)
    u = lambda p: -p[0]
    r = {
        'rDisco': (hib[0] - lob[0]) / 2, 'hDiscoSup': hib[2] - lob[2], 'hColumna': hic[2] - loc[2],
        'largoBloque': hi2[0] - lo2[0], 'anchoBloque': hi2[1] - lo2[1],
        'hBloque2': hi2[2] - lo2[2], 'hBloque1': hi1[2] - lo1[2], 'sepNiveles': (lo1[2] + hi1[2]) / 2 - h0,
        'espesorPlaca': hip[0] - lop[0], 'anchoPlaca': hip[1] - lop[1], 'altoPlaca': hip[2] - lop[2],
        'largoGuias': hip2[0] - lop[0],        # entre caras exteriores de las placas
        'zGuias': float(np.mean([abs((g[0][1] + g[1][1]) / 2) for g in guias])),
        'uA': u(A) - (u(lop) - (hip[0] - lop[0])), 'dhA': A[1] - h0,
        'hC': hie[2] - loe[2], 'dhC': C[1] - hie[2], 'uCBloque': u(C) - u(lo1),
        'L12': float(np.linalg.norm(B - C)), 'a': float(np.linalg.norm(B - A)), 'L9': float(np.linalg.norm(E - A)),
        'beta': math.degrees(math.atan2(B[1] - A[1], u(B) - u(A)) - math.atan2(E[1] - A[1], u(E) - u(A))),
        'L14': float(A2[1] - A[1]), 'L14_E': float(E2[1] - E[1]), 'L13': float(np.linalg.norm(A2 - E2)),
        'dg': -(lj[0] + hj[0]) / 2 - u(E), 'hg': E[1] - (lj[2] + hj[2]) / 2,
        'hCuerpoPinza': hsp[2] - lsp[2], 'pinzaBajoE': E[1] - lsp[2],
    }
    puntos = {k: [round(u(p), 2), round(p[1] - h0, 2)] for k, p in
              dict(A=A, B=B, C=C, E=E, A2=A2, E2=E2, TCP=np.array([(lj[0] + hj[0]) / 2, (lj[2] + hj[2]) / 2])).items()}
    ymedio = (lsp[1] + hsp[1]) / 2
    out = {'fuente': 'Inventor ensambleGeneral (STL por instancia), mm',
           'marco': {'R': np.round(R, 9).tolist(), 'o': np.round(o, 6).tolist(),
                     'nota': 'local = R·p - o (mm); x hacia atrás (la garra está en -x), y lateral, z arriba desde la cara '
                             'inferior del disco giratorio'},
           'pinza': {'y_plano_medio': round(float(ymedio), 3), 'mordaza_y_interior': round(float(hj[1]), 3),
                     'mordaza_u_trasera': round(float(-hj[0]), 3), 'cuerpo_u_delantera': round(float(-lsp[0]), 3)},
           'parametros': {k: round(float(v), 2) for k, v in r.items()},
           'pose': {'sX_geom': round(float(u(hip) - u(lo2)), 2),   # cara interior de la placa delantera - cara delantera del bloque 2
                    'bloque1_contra_placa': round(float(lo1[0] - hip[0]), 2)},
           'puntos_u_h_desde_eje_inferior': puntos,
           'z_eje_inferior_sobre_base_disco': round(float(h0), 2)}
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'medidas_inventor.json')
    json.dump(out, open(destino, 'w'), indent=2, ensure_ascii=False)
    print(json.dumps(out['parametros'], indent=1, ensure_ascii=False))


if __name__ == '__main__':
    raiz = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), *['..'] * 4))
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(raiz, 'global', 'modelo-3d', 'inventor', 'stl'))
