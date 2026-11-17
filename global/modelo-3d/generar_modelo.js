/*
 * Genera el modelo 3D articulado del brazo XK-JS1-1 a escala real (GLB).
 *
 *   node global/modelo-3d/generar_modelo.js
 *
 * Sin dependencias. Usa las piezas del modelo de Inventor del equipo
 * (inventor/stl/, un STL por instancia) y las acomoda en los nodos articulados
 * con las cotas de web/js/cinematica.js; solo el disco fijo de abajo, que no está
 * en el ensamble de Inventor, se dibuja con primitivas. Escribe el glTF binario a mano. Cada pieza móvil es un nodo con el origen en su eje de giro o
 * en su guía lineal; la jerarquía sigue el mecanismo:
 *
 *   brazo_xk_js1_1
 *   ├─ base_fija                       disco inferior 11 (fijo a la mesa)
 *   └─ base_giratoria      R  θ (eje Y del glTF)   disco superior, columna 7, bloque 2, NEMA 17
 *      └─ carro_x          P  sX (eje X)           placas 5 y 10, guías 16, husillos, NEMA 23
 *         ├─ carro_y       P  sY (eje X)           bloque 1, escuadra 6
 *         │  └─ biela_12   R  pasiva (pivote C)
 *         ├─ brazo_9       R  pasiva φ (pivote A)  brazo 9 + escuadra 8
 *         │  └─ pinza      R  γ - φ (pivote E: se inclina γ, no es paralelogramo)
 *         │     ├─ mordaza_izq / mordaza_der   garra ON/OFF (giran en el plano horizontal)
 *         │     └─ tcp     punto de trabajo
 *         └─ varilla_13    R  pasiva (pivote A', ángulo de la varilla 13)
 *
 * Las bielas pasivas no se animan a mano: la página calcula sus ángulos con la
 * cinemática (web/js/cinematica.js). Unidades del glTF: metros, Y hacia arriba,
 * X hacia adelante con θ = 0. Las cotas marcadas SUPUESTO están en cinematica.js.
 */
const fs = require('fs');
const path = require('path');
const K = require('../../web/js/cinematica.js');

const P = K.parametros, D = K.derivados;
const M = 0.001;   // mm -> m
const SALIDA = path.join(__dirname, 'brazo_xk-js1-1.glb');

// ------------------------------------------------------------------ materiales
const MATERIALES = [
  { name: 'aluminio', pbrMetallicRoughness: { baseColorFactor: [0.80, 0.82, 0.85, 1], metallicFactor: 0.55, roughnessFactor: 0.42 } },
  { name: 'acero', pbrMetallicRoughness: { baseColorFactor: [0.62, 0.65, 0.70, 1], metallicFactor: 0.9, roughnessFactor: 0.25 } },
  { name: 'motor', pbrMetallicRoughness: { baseColorFactor: [0.10, 0.10, 0.11, 1], metallicFactor: 0.3, roughnessFactor: 0.6 } },
  { name: 'acento', pbrMetallicRoughness: { baseColorFactor: [0.76, 0.38, 0.05, 1], metallicFactor: 0.1, roughnessFactor: 0.5 } },
  { name: 'sensor', pbrMetallicRoughness: { baseColorFactor: [0.85, 0.72, 0.30, 1], metallicFactor: 0.8, roughnessFactor: 0.35 } },
  { name: 'goma', pbrMetallicRoughness: { baseColorFactor: [0.18, 0.18, 0.2, 1], metallicFactor: 0, roughnessFactor: 0.9 } }
];
const MAT = Object.fromEntries(MATERIALES.map((m, i) => [m.name, i]));

// ------------------------------------------------------------------ geometría
// Cada pieza acumula triángulos por material: { mat: {pos:[], nor:[]} }
function nuevaGeo() { return {}; }
function tri(geo, mat, a, b, c, n) {
  const g = geo[mat] || (geo[mat] = { pos: [], nor: [] });
  if (!n) {
    const u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], v = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
    const l = Math.hypot(...n) || 1; n = n.map(x => x / l);
  }
  for (const p of [a, b, c]) { g.pos.push(p[0] * M, p[1] * M, p[2] * M); }
  const ns = Array.isArray(n[0]) ? n : [n, n, n];
  for (const x of ns) g.nor.push(...x);
}
function quad(geo, mat, a, b, c, d) { tri(geo, mat, a, b, c); tri(geo, mat, a, c, d); }

// Caja centrada en (cx, cy, cz) con lados (sx, sy, sz) [mm]
function caja(geo, mat, cx, cy, cz, sx, sy, sz) {
  const x0 = cx - sx / 2, x1 = cx + sx / 2, y0 = cy - sy / 2, y1 = cy + sy / 2, z0 = cz - sz / 2, z1 = cz + sz / 2;
  quad(geo, mat, [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]);
  quad(geo, mat, [x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0]);
  quad(geo, mat, [x1, y0, z1], [x1, y0, z0], [x1, y1, z0], [x1, y1, z1]);
  quad(geo, mat, [x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]);
  quad(geo, mat, [x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [x0, y1, z0]);
  quad(geo, mat, [x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]);
}

// Cilindro de radio r entre los puntos a y b (normales suaves en el manto)
function cilindro(geo, mat, a, b, r, seg) {
  const n = seg || 24;
  const eje = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
  const L = Math.hypot(...eje); const w = eje.map(x => x / L);
  const t = Math.abs(w[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
  let u = [w[1] * t[2] - w[2] * t[1], w[2] * t[0] - w[0] * t[2], w[0] * t[1] - w[1] * t[0]];
  const lu = Math.hypot(...u); u = u.map(x => x / lu);
  const v = [w[1] * u[2] - w[2] * u[1], w[2] * u[0] - w[0] * u[2], w[0] * u[1] - w[1] * u[0]];
  const dir = k => { const ang = 2 * Math.PI * k / n; return [0, 1, 2].map(i => Math.cos(ang) * u[i] + Math.sin(ang) * v[i]); };
  for (let k = 0; k < n; k++) {
    const d0 = dir(k), d1 = dir(k + 1);
    const p = (base, d) => [0, 1, 2].map(i => base[i] + r * d[i]);
    const a0 = p(a, d0), a1 = p(a, d1), b0 = p(b, d0), b1 = p(b, d1);
    tri(geo, mat, a0, a1, b1, [d0, d1, d1]);
    tri(geo, mat, a0, b1, b0, [d0, d1, d0]);
    tri(geo, mat, b, b0, b1, w);
    tri(geo, mat, a, a1, a0, w.map(x => -x));
  }
}

// Prisma: polígono convexo en el plano XY [[x, y], ...] (antihorario), extruido de z0 a z1
function prisma(geo, mat, poli, z0, z1) {
  const n = poli.length;
  for (let i = 1; i < n - 1; i++) {
    tri(geo, mat, [poli[0][0], poli[0][1], z1], [poli[i][0], poli[i][1], z1], [poli[i + 1][0], poli[i + 1][1], z1]);
    tri(geo, mat, [poli[0][0], poli[0][1], z0], [poli[i + 1][0], poli[i + 1][1], z0], [poli[i][0], poli[i][1], z0]);
  }
  for (let i = 0; i < n; i++) {
    const p = poli[i], q = poli[(i + 1) % n];
    quad(geo, mat, [p[0], p[1], z0], [q[0], q[1], z0], [q[0], q[1], z1], [p[0], p[1], z1]);
  }
}

// Barra plana con extremos redondeados entre (0,0) y (L,0), ancho w, en z ∈ [z0, z1]
function barra(geo, mat, L, w, z0, z1) {
  const poli = [], r = w / 2, s = 10;
  for (let k = 0; k <= s; k++) { const a = -Math.PI / 2 + Math.PI * k / s; poli.push([L + r * Math.cos(a), r * Math.sin(a)]); }
  for (let k = 0; k <= s; k++) { const a = Math.PI / 2 + Math.PI * k / s; poli.push([r * Math.cos(a), r * Math.sin(a)]); }
  prisma(geo, mat, poli, z0, z1);
}

const pasador = (geo, u, h, z0, z1) => cilindro(geo, 'acero', [u, h, z0], [u, h, z1], 4.5, 16);

// ------------------------------------------------------------------ mallas de Inventor
// Las piezas son las del modelo de Inventor del equipo, exportado a STL "un archivo por instancia"
// (inventor/stl/). medidas_inventor.json da el marco del ensamble (R, o) y la pose en que se exportó.
const DIR_STL = path.join(__dirname, 'inventor', 'stl');
const INV = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'semestres', '2026_II', 'modelo-3d',
  'levantamiento', 'medidas_inventor.json'), 'utf8'));

function leerStl(nombre) {
  const b = fs.readFileSync(path.join(DIR_STL, 'ensambleGeneral_1_' + nombre + '.stl'));
  const n = b.readUInt32LE(80), tris = [];
  for (let i = 0; i < n; i++) {
    const o = 84 + i * 50 + 12, t = [];
    for (let k = 0; k < 3; k++) t.push([b.readFloatLE(o + k * 12), b.readFloatLE(o + k * 12 + 4), b.readFloatLE(o + k * 12 + 8)]);
    tris.push(t);
  }
  return tris;
}

// Punto del STL -> mundo del glTF en mm (x = adelante, y = arriba desde la mesa, z = lateral) con θ = 0
const hSup = P.hDiscoInf + P.hEntreDiscos;                 // cara inferior del disco giratorio
function aMundo(v) {
  const R = INV.marco.R, o = INV.marco.o;
  const l = [0, 1, 2].map(i => R[i][0] * v[0] + R[i][1] * v[1] + R[i][2] * v[2] - o[i]);
  return [-l[0], l[2] + hSup, l[1]];
}

// Pose en que se exportó el ensamble (bastidor y bloque 1 contra la placa delantera)
const qRef = { theta: 0, sX: INV.pose.sX_geom - P.holgura, sY: -P.holgura };
const FR = K.directa(qRef);
const RAD = Math.PI / 180;

// Marco de cada nodo en esa pose: origen (mm, mundo) y giro alrededor de z
const ORIGEN = {};
function marco(nombre, o, ang) { ORIGEN[nombre] = { o, ang: (ang || 0) * RAD }; }
const tX = [D.u5_0 + qRef.sX, D.hEjeX, 0];                 // carro X (origen en la placa delantera, eje inferior)
const xBloque1_0 = -(D.carreraLibre - P.holgura);
const tY = [tX[0] + xBloque1_0 + FR.posBloque1, D.hEjeX, 0];
const hCrel = D.hCabs - D.hEjeX;
marco('base_giratoria', [0, 0, 0]);
marco('carro_x', tX);
marco('carro_y', tY);
marco('biela_12', [tY[0] + P.uCBloque, D.hEjeX + hCrel, 0], FR.angBiela);
marco('brazo_9', [FR.puntos.A.u, FR.puntos.A.h, 0], FR.phi);
marco('pinza', [FR.puntos.E.u, FR.puntos.E.h, 0], FR.gamma);
marco('varilla_13', [FR.puntos.A2.u, FR.puntos.A2.h, 0], FR.angVarilla);

function aLocal(nombre, w) {
  const m = ORIGEN[nombre], dx = w[0] - m.o[0], dy = w[1] - m.o[1], c = Math.cos(-m.ang), s = Math.sin(-m.ang);
  return [dx * c - dy * s, dx * s + dy * c, w[2] - m.o[2]];
}
function pieza(n, nombre, mat, transformar, enMarcoDe, espejo) {
  for (const t of leerStl(nombre)) {
    const v = t.map(p => (transformar || (w => w))(aLocal(enMarcoDe || n.nombre, aMundo(p))));
    if (espejo) v.reverse();                                 // un espejo invierte el sentido de las caras
    tri(n.geo, mat, v[0], v[1], v[2]);
  }
}

// ------------------------------------------------------------------ nodos
const nodos = [];
function nodo(nombre, padre, opciones) {
  const n = Object.assign({ nombre, padre, geo: nuevaGeo(), t: [0, 0, 0], extras: null }, opciones || {});
  nodos.push(n); return n;
}
const rel = (hijo, padre) => { const a = ORIGEN[hijo], b = ORIGEN[padre];      // traslación en el marco del padre
  const dx = a.o[0] - b.o[0], dy = a.o[1] - b.o[1], c = Math.cos(-b.ang), s = Math.sin(-b.ang);
  return [dx * c - dy * s, dx * s + dy * c, a.o[2] - b.o[2]]; };

const raiz = nodo('brazo_xk_js1_1', null);

// Base fija: disco inferior y buje (el ensamble de Inventor no los incluye)
const baseFija = nodo('base_fija', raiz);
cilindro(baseFija.geo, 'aluminio', [0, 0, 0], [0, P.hDiscoInf, 0], P.rDisco, 48);
cilindro(baseFija.geo, 'acero', [0, P.hDiscoInf, 0], [0, hSup, 0], 30, 32);

// Base giratoria (θ): disco, columnas y bloque 2
const giro = nodo('base_giratoria', raiz, { extras: { articulacion: 'revoluta', eje: 'y', variable: 'theta' } });
pieza(giro, 'baseBrazo_14', 'aluminio');
pieza(giro, 'baseCorredera_11', 'aluminio');
pieza(giro, 'baseCorredera_12', 'aluminio');
pieza(giro, 'BaseRodilloY_8', 'aluminio');

// Carro X: placas, guías, soporte del pivote A y poste de A'. Su traslación en el GLB es con sX = 0.
const cx = nodo('carro_x', giro, { t: [D.u5_0, D.hEjeX, 0], extras: { articulacion: 'prismatica', eje: 'x', variable: 'sX' } });
for (const k of ['soporteCorrederas_1', 'soporteCorrederas_2', 'Pieza14_10']) pieza(cx, k, 'aluminio');
for (const k of ['barraDesliz_3', 'barraDesliz_4', 'barraDesliz_5', 'barraDesliz_6', 'soporteRodillo_22']) pieza(cx, k, 'acero');

// Carro Y: bloque 1 y escuadra 6. Su traslación en el GLB es con el bloque 1 en g = 0.
const cyN = nodo('carro_y', cx, { t: [xBloque1_0, 0, 0], extras: { articulacion: 'prismatica', eje: 'x', variable: 'sY' } });
pieza(cyN, 'BaseRodilloY_7', 'aluminio');
pieza(cyN, 'soporteBarrasBrazo_9', 'aluminio');

const biela = nodo('biela_12', cyN, { t: rel('biela_12', 'carro_y'), extras: { articulacion: 'revoluta', eje: 'z', pasiva: true } });
pieza(biela, 'barraBrazo2_19', 'aluminio');

const brazo = nodo('brazo_9', cx, { t: rel('brazo_9', 'carro_x'), extras: { articulacion: 'revoluta', eje: 'z', pasiva: true, variable: 'phi' } });
pieza(brazo, 'barraBrazo1_13', 'aluminio');
pieza(brazo, 'soporteBarrasBrazo_20', 'aluminio');

// Pinza: origen en E. La página le aplica γ - φ (cuadrilátero A-A'-E'-E, no paralelogramo).
const pinza = nodo('pinza', brazo, { t: [P.L9, 0, 0], extras: { articulacion: 'revoluta', eje: 'z', pasiva: true, nota: 'rotación = gamma - phi' } });
pieza(pinza, 'soportePinza_17', 'aluminio');
pieza(pinza, 'trasePinza_18', 'aluminio');
pieza(pinza, 'soporteRodillo_21', 'acero');

// Mordazas: la 15 está cerrada en el STL; la derecha es su espejo respecto del plano medio del cuerpo.
// Pivote (SUPUESTO): en el extremo trasero de cada mordaza, dentro del cuerpo, del lado exterior.
const PZ = INV.pinza;
const zMedio = PZ.y_plano_medio;                          // coordenada lateral del plano medio (mundo, mm)
const uPiv = PZ.mordaza_u_trasera + (PZ.cuerpo_u_delantera - PZ.mordaza_u_trasera) / 2 - FR.puntos.E.u;
const anchoMordaza = Math.abs(PZ.mordaza_y_interior - zMedio) + 29;  // 29 mm de ancho de la mordaza
for (const [nombre, s] of [['mordaza_izq', 1], ['mordaza_der', -1]]) {
  const zPiv = s * -(anchoMordaza - 2);                    // borde exterior (relativo al plano medio)
  const m = nodo(nombre, pinza, {
    t: [uPiv, -P.hg, zPiv],
    extras: { articulacion: 'revoluta', eje: 'y', garra: true, apertura_grados: 25 }
  });
  pieza(m, 'pinza_15', 'aluminio', v => {
    // v está en el marco de la pinza; se lleva al plano medio, se espeja si hace falta y se pasa al pivote
    const z = (v[2] - zMedio) * s;
    return [v[0] - uPiv, v[1] + P.hg, z - zPiv];
  }, 'pinza', s < 0);
}
nodo('tcp', pinza, { t: [P.dg, -P.hg, 0] });

const varilla = nodo('varilla_13', cx, { t: rel('varilla_13', 'carro_x'), extras: { articulacion: 'revoluta', eje: 'z', pasiva: true } });
pieza(varilla, 'barillaBrazo_23', 'acero');

// ------------------------------------------------------------------ glTF binario
function escribirGlb() {
  const gltf = {
    asset: { version: '2.0', generator: 'generar_modelo.js (Brazo 4 GDL, UMSA)' },
    scene: 0, scenes: [{ name: 'brazo', nodes: [0] }],
    nodes: [], meshes: [], materials: MATERIALES, accessors: [], bufferViews: [], buffers: []
  };
  const trozos = []; let largo = 0;
  function vista(arr, target) {
    const buf = Buffer.from(arr.buffer, arr.byteOffset, arr.byteLength);
    const relleno = (4 - (largo % 4)) % 4;
    if (relleno) { trozos.push(Buffer.alloc(relleno)); largo += relleno; }
    gltf.bufferViews.push({ buffer: 0, byteOffset: largo, byteLength: buf.length, target });
    trozos.push(buf); largo += buf.length;
    return gltf.bufferViews.length - 1;
  }
  nodos.forEach((n, i) => {
    const g = { name: n.nombre };
    if (n.t.some(v => v)) g.translation = n.t.map(v => v * M);
    if (n.extras) g.extras = n.extras;
    const hijos = nodos.map((x, j) => x.padre === n ? j : -1).filter(j => j >= 0);
    if (hijos.length) g.children = hijos;
    const prims = [];
    for (const [mat, data] of Object.entries(n.geo)) {
      const pos = new Float32Array(data.pos), nor = new Float32Array(data.nor);
      const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
      for (let k = 0; k < pos.length; k += 3) for (let c = 0; c < 3; c++) { min[c] = Math.min(min[c], pos[k + c]); max[c] = Math.max(max[c], pos[k + c]); }
      gltf.accessors.push({ bufferView: vista(pos, 34962), componentType: 5126, count: pos.length / 3, type: 'VEC3', min, max });
      const ip = gltf.accessors.length - 1;
      gltf.accessors.push({ bufferView: vista(nor, 34962), componentType: 5126, count: nor.length / 3, type: 'VEC3' });
      prims.push({ attributes: { POSITION: ip, NORMAL: ip + 1 }, material: MAT[mat] });
    }
    if (prims.length) { gltf.meshes.push({ name: n.nombre, primitives: prims }); g.mesh = gltf.meshes.length - 1; }
    gltf.nodes.push(g);
  });
  const bin = Buffer.concat(trozos);
  gltf.buffers.push({ byteLength: bin.length });
  let json = Buffer.from(JSON.stringify(gltf), 'utf8');
  json = Buffer.concat([json, Buffer.alloc((4 - json.length % 4) % 4, 0x20)]);
  const binPad = Buffer.concat([bin, Buffer.alloc((4 - bin.length % 4) % 4)]);
  const cab = Buffer.alloc(12);
  cab.writeUInt32LE(0x46546C67, 0); cab.writeUInt32LE(2, 4);
  cab.writeUInt32LE(12 + 8 + json.length + 8 + binPad.length, 8);
  const c1 = Buffer.alloc(8); c1.writeUInt32LE(json.length, 0); c1.writeUInt32LE(0x4E4F534A, 4);
  const c2 = Buffer.alloc(8); c2.writeUInt32LE(binPad.length, 0); c2.writeUInt32LE(0x004E4942, 4);
  fs.writeFileSync(SALIDA, Buffer.concat([cab, c1, json, c2, binPad]));
  const tris = nodos.reduce((s, n) => s + Object.values(n.geo).reduce((t, d) => t + d.pos.length / 9, 0), 0);
  console.log(`${path.basename(SALIDA)}: ${nodos.length} nodos, ${tris} triángulos, ${(fs.statSync(SALIDA).size / 1024).toFixed(0)} KB`);
}

escribirGlb();
