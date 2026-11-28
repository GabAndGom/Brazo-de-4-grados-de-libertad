// Dashboard del ERP (laboratorio 7): lee la API /api/v1 de la app, que consulta PostgreSQL.
// Gráficos propios en canvas (sin librerías, la app funciona sin internet): un gráfico por variable,
// cada uno con su propia escala y unidad, cruz y valor al pasar el puntero.
// RBAC: el observador solo lee; «Rearmar planta» y el registro de ingresos son solo del operador
// (la vista los oculta y el servidor los vuelve a comprobar).
'use strict';
const $ = (id) => document.getElementById(id);
const VARIABLES = [
  { tag: 'ZI-102', nombre: 'Carro X (alcance)', unidad: 'mm' },
  { tag: 'ZI-103', nombre: 'Carro Y (altura)', unidad: 'mm' },
  { tag: 'ZI-101', nombre: 'Base θ', unidad: '°' },
  { tag: 'SY-100', nombre: 'Tren de pulsos X/Y', unidad: 'Hz' },
  { tag: 'SY-101', nombre: 'Tren de pulsos de la base', unidad: 'Hz' },
];
let yo = { rol: 'observador' };
let series = {};
const graficos = {};

async function api(ruta, opciones) {
  const r = await fetch(ruta, Object.assign({ credentials: 'same-origin' }, opciones));
  if (r.status === 401) { location.href = 'login'; throw new Error('sesión vencida'); }
  const d = await r.json();
  if (!d.ok) throw new Error(d.error || ('error ' + r.status));
  return d.datos !== undefined ? d.datos : d;
}

function celda(texto, clase) { const td = document.createElement('td'); td.textContent = texto ?? '—'; if (clase) td.className = clase; return td; }
function hora(iso) { return iso ? new Date(iso).toLocaleString('es-BO', { dateStyle: 'short', timeStyle: 'medium' }) : '—'; }

function tabla(contenedor, columnas, filas) {
  const caja = $(contenedor);
  caja.replaceChildren();
  if (!filas.length) { const p = document.createElement('p'); p.className = 'vacio'; p.textContent = 'Sin registros.'; caja.append(p); return; }
  const t = document.createElement('table');
  const cab = t.createTHead().insertRow();
  columnas.forEach(([titulo]) => { const th = document.createElement('th'); th.textContent = titulo; cab.append(th); });
  const cuerpo = t.createTBody();
  filas.forEach((f) => { const tr = cuerpo.insertRow(); columnas.forEach(([, valor, clase]) => tr.append(celda(valor(f), clase))); });
  caja.append(t);
}

// ------------------------------------------------------------------ indicadores
function kpis(k) {
  const tiles = [
    ['Eficiencia homeostática', k.eficiencia_homeostatica == null ? '—' : (100 * k.eficiencia_homeostatica).toFixed(2) + ' %',
      `${k.horas_con_alarma} h con alarma de ${k.horas_operacion} h`],
    ['Horas en operación', k.horas_operacion.toFixed(2), `${k.ciclos} ciclos de operación`],
    ['Órdenes aceptadas', k.porcentaje_aceptadas == null ? '—' : (100 * k.porcentaje_aceptadas).toFixed(1) + ' %',
      `${k.ordenes_aceptadas} de ${k.ordenes} órdenes`],
    ['Alarmas activas', String(k.alarmas_activas), 'último evento de cada alarma'],
    ['Muestras guardadas', k.muestras.toLocaleString('es-BO'), '1 por segundo y por variable'],
  ];
  $('kpis').replaceChildren(...tiles.map(([n, v, nota]) => {
    const d = document.createElement('div'); d.className = 'sd-tarjeta kpi';
    d.innerHTML = '<div class="nombre"></div><div class="valor"></div><div class="nota"></div>';
    d.querySelector('.nombre').textContent = n; d.querySelector('.valor').textContent = v; d.querySelector('.nota').textContent = nota;
    return d;
  }));
  $('formula').textContent = 'Eficiencia homeostática: ' + k.formula + '. Propuesta del equipo; debe acordarse con el docente.';
  const p = $('planta');
  p.className = 'sd-pastilla ' + (k.planta_en_operacion ? 'ok' : 'mal');
  p.textContent = k.planta_en_operacion ? 'Planta en operación' : 'Planta fuera de operación (trigger)';
  $('rearmar').hidden = yo.rol !== 'operador' || k.planta_en_operacion;
}

// ------------------------------------------------------------------ gráficos
function crearGraficos() {
  VARIABLES.forEach((v) => {
    const tarjeta = document.createElement('div');
    tarjeta.className = 'sd-tarjeta grafico';
    tarjeta.innerHTML = '<h3></h3><canvas role="img"></canvas><div class="tip"></div>';
    tarjeta.querySelector('h3').innerHTML = '<b></b><span></span>';
    tarjeta.querySelector('h3 b').textContent = `${v.nombre} · ${v.tag}`;
    const canvas = tarjeta.querySelector('canvas');
    canvas.setAttribute('aria-label', `${v.nombre} en ${v.unidad}`);
    $('graficos').append(tarjeta);
    const g = { v, canvas, tip: tarjeta.querySelector('.tip'), resumen: tarjeta.querySelector('h3 span'), puntos: [], cursor: null };
    graficos[v.tag] = g;
    const mover = (ev) => { const r = canvas.getBoundingClientRect(); g.cursor = ev.clientX - r.left; dibujar(g); };
    canvas.addEventListener('pointermove', mover);
    canvas.addEventListener('pointerdown', mover);
    canvas.addEventListener('pointerleave', () => { g.cursor = null; dibujar(g); });
  });
  new ResizeObserver(() => Object.values(graficos).forEach(dibujar)).observe($('graficos'));
}

function colores() {
  const c = getComputedStyle(document.body);
  return { linea: c.getPropertyValue('--c-acento').trim(), eje: c.getPropertyValue('--c-borde').trim(),
           texto: c.getPropertyValue('--c-texto-2').trim(), fondo: c.getPropertyValue('--c-superficie').trim() };
}

function dibujar(g) {
  const { canvas } = g;
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.clientWidth, H = canvas.clientHeight;
  if (!W) return;
  canvas.width = W * dpr; canvas.height = H * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  const col = colores();
  const m = { izq: 52, der: 10, arr: 8, aba: 22 };
  const p = g.puntos;
  ctx.font = '12px system-ui, sans-serif';
  ctx.fillStyle = col.texto;
  if (!p.length) { ctx.fillText('Sin datos en el periodo', m.izq, H / 2); g.tip.style.display = 'none'; return; }
  const t0 = p[0].t, t1 = Math.max(p[p.length - 1].t, t0 + 1);
  let y0 = Math.min(...p.map((q) => q.y)), y1 = Math.max(...p.map((q) => q.y));
  if (y1 - y0 < 1e-9) { y0 -= 1; y1 += 1; }
  const paso = pasoRedondo((y1 - y0) / 3);          // escala con valores redondos (1, 2 o 5 × 10^n)
  y0 = Math.floor(y0 / paso) * paso; y1 = Math.ceil(y1 / paso) * paso;
  const marcas = Math.round((y1 - y0) / paso);
  const X = (t) => m.izq + (t - t0) / (t1 - t0) * (W - m.izq - m.der);
  const Y = (y) => H - m.aba - (y - y0) / (y1 - y0) * (H - m.arr - m.aba);
  // rejilla y escala (recesivas)
  ctx.strokeStyle = col.eje; ctx.lineWidth = 1;
  for (let i = 0; i <= marcas; i++) {
    const v = y0 + paso * i, yy = Math.round(Y(v)) + 0.5;
    ctx.beginPath(); ctx.moveTo(m.izq, yy); ctx.lineTo(W - m.der, yy); ctx.stroke();
    ctx.fillText(formato(v), 4, yy + 4);
  }
  ctx.fillText(new Date(t0).toLocaleTimeString('es-BO'), m.izq, H - 5);
  const fin = new Date(t1).toLocaleTimeString('es-BO');
  ctx.fillText(fin, W - m.der - ctx.measureText(fin).width, H - 5);
  // serie (línea de 2 px)
  ctx.strokeStyle = col.linea; ctx.lineWidth = 2; ctx.lineJoin = 'round';
  ctx.beginPath();
  p.forEach((q, i) => { const x = X(q.t), y = Y(q.y); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
  ctx.stroke();
  // cruz y valor
  if (g.cursor == null) { g.tip.style.display = 'none'; return; }
  const tc = t0 + (g.cursor - m.izq) / (W - m.izq - m.der) * (t1 - t0);
  let k = 0;
  for (let i = 1; i < p.length; i++) if (Math.abs(p[i].t - tc) < Math.abs(p[k].t - tc)) k = i;
  const x = X(p[k].t), y = Y(p[k].y);
  ctx.strokeStyle = col.texto; ctx.lineWidth = 1; ctx.setLineDash([3, 3]);
  ctx.beginPath(); ctx.moveTo(x, m.arr); ctx.lineTo(x, H - m.aba); ctx.stroke(); ctx.setLineDash([]);
  ctx.fillStyle = col.linea; ctx.strokeStyle = col.fondo; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(x, y, 4.5, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
  g.tip.textContent = `${formato(p[k].y)} ${g.v.unidad} · ${new Date(p[k].t).toLocaleTimeString('es-BO')}`;
  g.tip.style.display = 'block';
  const ancho = g.tip.offsetWidth;
  g.tip.style.left = Math.min(Math.max(x + 16 - ancho / 2, 8), W + 16 - ancho - 8) + 'px';
  g.tip.style.top = (y + 24 > H - 10 ? y - 12 : y + 44) + 'px';
}

function formato(v) { return Math.abs(v) >= 1000 ? String(Math.round(v)) : String(Math.round(v * 100) / 100).replace('.', ','); }
function pasoRedondo(x) { const e = Math.pow(10, Math.floor(Math.log10(x))); const f = x / e; return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * e; }

// ------------------------------------------------------------------ carga
function rango() {
  const [s, cada] = $('periodo').value.split('|').map(Number);
  const hasta = new Date(), desde = new Date(hasta - s * 1000);
  return { desde: desde.toISOString(), hasta: hasta.toISOString(), cada };
}

async function cargarSeries() {
  const r = rango();
  const q = `desde=${encodeURIComponent(r.desde)}&hasta=${encodeURIComponent(r.hasta)}&cada=${r.cada}&limite=100000`;
  $('csv').href = `api/v1/telemetria/planta/1?${q}&formato=csv`;
  const filas = await api(`api/v1/telemetria/planta/1?${q}`);
  series = {};
  filas.forEach((f) => (series[f.tag] = series[f.tag] || []).push({ t: Date.parse(f.instante), y: f.valor }));
  VARIABLES.forEach((v) => {
    const g = graficos[v.tag];
    g.puntos = series[v.tag] || [];
    const ult = g.puntos[g.puntos.length - 1];
    g.resumen.textContent = ult ? `actual ${formato(ult.y)} ${v.unidad} · ${g.puntos.length} puntos` : 'sin datos';
    dibujar(g);
  });
}

async function cargarTablas() {
  const [activas, alarmas, ordenes] = await Promise.all([api('api/v1/alertas/activas'), api('api/v1/alertas?limite=15'), api('api/v1/ordenes?limite=15')]);
  const sev = (s) => ['', 'aviso', 'falla', 'crítica'][s] || s;
  tabla('t-activas', [['Alarma', (f) => f.codigo], ['Severidad', (f) => sev(f.severidad)], ['Desde', (f) => hora(f.instante), 'num'], ['Detalle', (f) => f.detalle]], activas);
  tabla('t-alarmas', [['Instante', (f) => hora(f.instante), 'num'], ['Alarma', (f) => f.codigo], ['Estado', (f) => (f.activa ? 'activa' : 'despejada')], ['Detalle', (f) => f.detalle]], alarmas);
  tabla('t-ordenes', [['Instante', (f) => hora(f.instante), 'num'], ['Orden', (f) => f.tipo], ['Resultado', (f) => (f.aceptada ? 'aceptada' : 'rechazada')], ['Motivo', (f) => f.motivo]], ordenes);
  if (yo.rol === 'operador') {
    $('caja-sesiones').hidden = false;
    const s = await api('api/v1/sesiones?limite=15');
    tabla('t-sesiones', [['Instante', (f) => hora(f.instante), 'num'], ['Usuario', (f) => f.usuario], ['IP', (f) => f.ip], ['Resultado', (f) => (f.exito ? 'ingresó' : 'fallido')]], s);
  }
}

async function actualizar() {
  try {
    const [k] = await Promise.all([api('api/v1/kpi?dias=7'), cargarSeries()]);
    kpis(k);
    await cargarTablas();
    $('estado').textContent = 'Actualizado ' + new Date().toLocaleTimeString('es-BO');
  } catch (e) {
    $('estado').textContent = 'Error: ' + e.message;
  }
}

async function iniciar() {
  try {
    yo = await api('api/v1/yo');
  } catch (e) { $('estado').textContent = 'Error: ' + e.message; }
  $('quien').textContent = `${yo.usuario || ''} · ${yo.rol}`;
  crearGraficos();
  $('periodo').addEventListener('change', actualizar);
  $('rearmar').addEventListener('click', async () => {
    if (!confirm('¿Volver a poner la planta en operación? Revise antes la alarma que la detuvo.')) return;
    try { await api('api/v1/planta/rearmar', { method: 'POST' }); actualizar(); } catch (e) { $('estado').textContent = 'Error: ' + e.message; }
  });
  actualizar();
  setInterval(() => { if (!document.hidden && Number($('periodo').value.split('|')[0]) <= 3600) actualizar(); }, 5000);
}
iniciar();
