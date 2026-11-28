# Presentación de 15 min: control y gemelo digital del brazo XK-JS1-1 (28/11/2026)
import json, os
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

D = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(D, 'img')
NAVY = RGBColor(0x12, 0x26, 0x3A); TEAL = RGBColor(0x0F, 0x76, 0x6E); NAR = RGBColor(0xE8, 0x77, 0x2E)
GRIS = RGBColor(0x5B, 0x65, 0x72); CLARO = RGBColor(0xF3, 0xF5, 0xF7); BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
TEAL_C = RGBColor(0xE3, 0xF2, 0xF0); NAR_C = RGBColor(0xFD, 0xEE, 0xE3); AZ_C = RGBColor(0xE6, 0xEC, 0xF3)
ROJO = RGBColor(0xB4, 0x23, 0x18); TXT = RGBColor(0x1F, 0x29, 0x33)
FUENTE = 'Calibri'

prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
VACIA = prs.slide_layouts[6]
DATOS = []          # para el documento: título, tiempo, guion, explicación
TOTAL = [0]


def txt(sl, x, y, w, h, texto, tam=16, color=TXT, negrita=False, alin=PP_ALIGN.LEFT, ancla=MSO_ANCHOR.TOP,
        cursiva=False, fuente=FUENTE):
    tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame
    tf.word_wrap = True; tf.vertical_anchor = ancla
    tf.margin_left = tf.margin_right = Inches(0.04); tf.margin_top = tf.margin_bottom = Inches(0.02)
    for i, linea in enumerate(texto.split('\n')):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = alin
        r = p.add_run(); r.text = linea; f = r.font
        f.size = Pt(tam); f.color.rgb = color; f.bold = negrita; f.italic = cursiva; f.name = fuente
    return tb


def puntos(sl, x, y, w, h, items, tam=15, sep=6, color=TXT, vineta='■', col_v=TEAL):
    """items: str o (negrita, resto) o ('-', texto) para sub-punto."""
    tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.04)
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.space_after = Pt(sep)
        sub = isinstance(it, tuple) and it[0] == '-'
        r = p.add_run(); r.text = ('      – ' if sub else vineta + '  '); r.font.size = Pt(tam - (3 if not sub else 1))
        r.font.color.rgb = GRIS if sub else col_v; r.font.name = FUENTE
        if isinstance(it, tuple) and not sub:
            r = p.add_run(); r.text = it[0]; r.font.bold = True; r.font.size = Pt(tam); r.font.color.rgb = NAVY; r.font.name = FUENTE
            r = p.add_run(); r.text = it[1]; r.font.size = Pt(tam); r.font.color.rgb = color; r.font.name = FUENTE
        else:
            r = p.add_run(); r.text = it[1] if sub else it; r.font.size = Pt(tam - (1 if sub else 0))
            r.font.color.rgb = GRIS if sub else color; r.font.name = FUENTE
    return tb


def rect(sl, x, y, w, h, relleno, borde=None, forma=MSO_SHAPE.RECTANGLE, grosor=1.25):
    s = sl.shapes.add_shape(forma, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = relleno
    if borde is None: s.line.fill.background()
    else: s.line.color.rgb = borde; s.line.width = Pt(grosor)
    s.shadow.inherit = False
    if forma == MSO_SHAPE.ROUNDED_RECTANGLE: s.adjustments[0] = 0.12
    return s


def caja(sl, x, y, w, h, titulo, cuerpo='', relleno=AZ_C, borde=NAVY, tt=14, tc=11.5, col_t=NAVY):
    s = rect(sl, x, y, w, h, relleno, borde, MSO_SHAPE.ROUNDED_RECTANGLE)
    tf = s.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for m in ('margin_left', 'margin_right'): setattr(tf, m, Inches(0.08))
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = titulo; r.font.bold = True; r.font.size = Pt(tt); r.font.color.rgb = col_t; r.font.name = FUENTE
    for linea in cuerpo.split('\n') if cuerpo else []:
        p = tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = linea; r.font.size = Pt(tc); r.font.color.rgb = TXT; r.font.name = FUENTE
    return s


def flecha(sl, x1, y1, x2, y2, color=GRIS, doble=False, grosor=2):
    c = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color; c.line.width = Pt(grosor)
    ln = c.line._get_or_add_ln()
    for tag in (['a:tailEnd', 'a:headEnd'] if doble else ['a:tailEnd']):
        e = ln.makeelement(qn(tag), {'type': 'triangle', 'w': 'med', 'len': 'med'}); ln.append(e)
    return c


def img(sl, nombre, x, y, w=None, h=None, borde=False, recorte=None):
    ruta = os.path.join(IMG, nombre)
    if recorte:
        im = Image.open(ruta); ruta = os.path.join(IMG, '_r_' + nombre); im.crop(recorte).save(ruta)
    iw, ih = Image.open(ruta).size
    if w and h:
        if iw / ih > w / h: hh = w * ih / iw; y += (h - hh) / 2; h = hh
        else: ww = h * iw / ih; x += (w - ww) / 2; w = ww
    elif w: h = w * ih / iw
    else: w = h * iw / ih
    p = sl.shapes.add_picture(ruta, Inches(x), Inches(y), Inches(w), Inches(h))
    if borde: p.line.color.rgb = RGBColor(0xCF, 0xD6, 0xDE); p.line.width = Pt(1)
    return p


def pie(sl, texto, x, y, w):
    txt(sl, x, y, w, 0.3, texto, 10.5, GRIS, cursiva=True, alin=PP_ALIGN.CENTER)


def lamina(seccion, titulo, segundos, guion, explicacion):
    sl = prs.slides.add_slide(VACIA); n = len(prs.slides)
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = BLANCO
    rect(sl, 0, 0, 0.16, 7.5, TEAL)
    txt(sl, 0.55, 0.32, 9, 0.35, seccion.upper(), 12, TEAL, True)
    txt(sl, 0.55, 0.62, 12.2, 0.75, titulo, 28, NAVY, True)
    rect(sl, 0.58, 1.36, 1.1, 0.05, NAR)
    rect(sl, 0.16, 7.08, 13.18, 0.42, CLARO)
    txt(sl, 0.55, 7.13, 9, 0.3, 'Brazo XK-JS1-1 de 4 GDL · Control y gemelo digital · Mención Control · 28/11/2026', 10.5, GRIS)
    pill = rect(sl, 12.25, 7.13, 0.7, 0.3, NAVY, forma=MSO_SHAPE.ROUNDED_RECTANGLE); pill.adjustments[0] = 0.5
    tf = pill.text_frame; tf.margin_top = tf.margin_bottom = 0; p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = f'{n:02d}'; r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = BLANCO; r.font.name = FUENTE
    notas(sl, n, titulo, segundos, guion)
    DATOS.append({'n': n, 'titulo': titulo, 'seccion': seccion, 'segundos': segundos, 'guion': guion,
                  'explicacion': explicacion})
    return sl


def notas(sl, n, titulo, segundos, guion):
    ini = TOTAL[0]; TOTAL[0] += segundos
    m = lambda s: f'{s // 60}:{s % 60:02d}'
    sl.notes_slide.notes_text_frame.text = (f'[{m(ini)} – {m(TOTAL[0])}]  ({segundos} s)\n\n' + guion)


# ============================================================== 1. Portada
sl = prs.slides.add_slide(VACIA)
sl.background.fill.solid(); sl.background.fill.fore_color.rgb = NAVY
img(sl, 'brazo_vista_general.jpg', 7.35, 0, 5.983, 7.5, recorte=(330, 0, 1290, 1005))
rect(sl, 7.35, 0, 0.08, 7.5, NAR)
txt(sl, 0.7, 0.55, 6.4, 0.6, 'UNIVERSIDAD MAYOR DE SAN ANDRÉS\nFACULTAD DE INGENIERÍA · INGENIERÍA ELECTRÓNICA', 12, RGBColor(0xB8, 0xC7, 0xD6), True)
txt(sl, 0.7, 1.55, 6.4, 0.4, 'MUESTRA DEL TRABAJO · MENCIÓN CONTROL', 14, NAR, True)
txt(sl, 0.7, 2.0, 6.5, 1.9, 'Control y gemelo digital\ndel brazo robótico XK-JS1-1\nde 4 grados de libertad', 34, BLANCO, True)
rect(sl, 0.72, 4.05, 1.3, 0.06, NAR)
txt(sl, 0.7, 4.25, 6.4, 0.7, 'Sistemas de Control II ETN-902 · Técnicas de Control ETN-1034', 14, RGBColor(0xDD, 0xE6, 0xEE))
txt(sl, 0.7, 4.85, 6.4, 1.6, 'Gabriel Andres Gomez Calla · Jose Lenin Mamani Choque\nMiguel Alejandro Lima Huarachi · Román Abner Machicado Arequipa\nMarco Eduardo Chura Rondo',
    12.5, RGBColor(0xB8, 0xC7, 0xD6))
txt(sl, 0.7, 6.55, 6.4, 0.4, 'Escuadra 4GDL · La Paz, 28 de noviembre de 2026', 12.5, BLANCO, True)
notas(sl, 1, 'Portada', 30,
      'Buenos días. Somos la Escuadra 4GDL y vamos a mostrar el trabajo hecho este semestre sobre el brazo robótico '
      'XK-JS1-1 del laboratorio, visto desde la mención de control: cómo está instrumentado, cómo se modela, qué '
      'controladores se pueden diseñar con el hardware que tiene, y el gemelo digital que construimos para '
      'supervisarlo y operarlo. Al final haremos una demostración en vivo de la aplicación.')
DATOS.append({'n': 1, 'titulo': 'Control y gemelo digital del brazo XK-JS1-1', 'seccion': 'Portada', 'segundos': 30,
              'guion': sl.notes_slide.notes_text_frame.text.split('\n\n', 1)[1],
              'explicacion': 'Presenta el tema, el equipo y las materias del área de control a las que responde el '
                             'trabajo (ETN-902 y ETN-1034). La foto es la planta real del laboratorio.'})

# ============================================================== 2. Objetivo y agenda
sl = lamina('Introducción', 'De una maqueta sin documentación a una planta modelada y supervisada', 45,
            'El punto de partida fue una maqueta que funcionaba con un programa heredado, sin planos confiables ni '
            'modelo. El objetivo fue convertirla en una planta de control: documentada con normas, modelada, '
            'analizada y supervisada por un gemelo digital. La presentación sigue ese mismo orden: primero la planta '
            'y su instrumentación, después la estructura de control y el modelo, luego los controladores diseñados, '
            'el gemelo digital y, por último, la demostración.',
            'El objetivo del trabajo y el orden de la exposición. La columna de la derecha sirve de mapa: cada bloque '
            'corresponde a una parte del ciclo clásico de un ingeniero de control (planta → instrumentación → '
            'modelo → análisis → diseño → implementación y supervisión).')
caja(sl, 0.6, 1.75, 5.6, 2.15, 'Objetivo',
     'Convertir el brazo del laboratorio en una planta de control\ndocumentada (ISA-5.1 / IEC 60617), modelada,\nanalizada '
     'y supervisada por un gemelo digital\nconectado al PLC real.', TEAL_C, TEAL, 18, 15, TEAL)
caja(sl, 0.6, 4.1, 5.6, 2.7, 'Enfoque de control',
     'Planta → sensores y actuadores → modelo\n→ propiedades estructurales → diseño (PI, LQR)\n→ implementación en el PLC y supervisión\n\n'
     'Todo lo que se diseñó se validó en simulación;\nlo que depende de hardware que falta se indica.', AZ_C, NAVY, 18, 14)
agenda = [('1', 'La planta y su instrumentación', 'P&ID, esquema eléctrico, E/S'), ('2', 'Estructura de control actual', 'lazo abierto con trenes de pulsos'),
          ('3', 'Modelo y análisis', 'identificación, espacio de estados, controlabilidad'), ('4', 'Diseño de controladores', 'PI discreto y LQR'),
          ('5', 'Gemelo digital', 'qué es, cómo funciona, acceso por red'), ('6', 'Demostración en vivo', 'simulación, red y observadores libres'),
          ('7', 'Conclusiones y trabajo futuro', '')]
for i, (k, t, s) in enumerate(agenda):
    y = 1.75 + i * 0.73
    c = rect(sl, 6.75, y, 0.55, 0.55, NAR if k == '5' or k == '6' else NAVY, forma=MSO_SHAPE.OVAL)
    tf = c.text_frame; p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = k; r.font.bold = True; r.font.size = Pt(16); r.font.color.rgb = BLANCO; r.font.name = FUENTE
    txt(sl, 7.45, y - 0.02, 5.4, 0.35, t, 17, NAVY, True)
    if s: txt(sl, 7.45, y + 0.29, 5.4, 0.3, s, 12.5, GRIS)

# ============================================================== 3. La planta
sl = lamina('1 · La planta', 'Brazo XK-JS1-1: tres ejes con motores paso a paso y una garra', 60,
            'La planta tiene tres ejes y una garra. La base gira con un motor NEMA 17 y una reducción de 5 a 1; los '
            'carros X e Y son husillos de 5 milímetros por vuelta movidos por motores NEMA 23. Los drivers JMC trabajan '
            'a 1000 pulsos por vuelta, así que cada pulso son 5 micras en los carros. El controlador es un PLC S7-200 '
            'CPU 224, que tiene solo dos salidas de tren de pulsos: Q0.0 para la base y Q0.1 compartida por los dos '
            'carros. Los sensores son discretos: finales de carrera en X e Y y un inductivo que marca el cero de la '
            'base. No hay ningún sensor continuo de posición, y eso va a condicionar todo el análisis de control.',
            'Los componentes de la planta agrupados por función de control. Lo esencial para el resto de la '
            'presentación: (1) los actuadores son motores paso a paso, que se mandan por número de pulsos; (2) el '
            'PLC tiene dos generadores de trenes de pulsos (PTO) para tres ejes; (3) todos los sensores son binarios '
            '(finales de carrera e inductivo), no hay medición continua de la posición.')
img(sl, 'brazo_vista_general.jpg', 0.6, 1.65, 5.2, 5.2, borde=True)
filas = [('Eje', 'Actuador', 'Sensor', 'Resolución'),
         ('Base θ', 'NEMA 17 + JMC 2M530\nreducción 5:1', 'inductivo I0.0\n(cero)', '9,17·10⁻⁵ rad/pulso'),
         ('Carro X (alcance)', 'NEMA 23 + JMC 2M542\nhusillo 5 mm/vuelta', 'finales I0.1 / I0.2', '0,005 mm/pulso\n170 mm'),
         ('Carro Y (altura)', 'NEMA 23 + JMC 2M542\nhusillo 5 mm/vuelta', 'finales I0.3 / I0.4', '0,005 mm/pulso\n170 mm'),
         ('Garra', 'solenoide (Q0.7)', '—', 'ON / OFF')]
tb = sl.shapes.add_table(len(filas), 4, Inches(6.1), Inches(1.65), Inches(6.75), Inches(3.4)).table
anchos = [1.55, 2.2, 1.55, 1.45]
for j, a in enumerate(anchos): tb.columns[j].width = Inches(a)
for i, f in enumerate(filas):
    for j, v in enumerate(f):
        c = tb.cell(i, j); c.text = v; c.fill.solid(); c.fill.fore_color.rgb = NAVY if i == 0 else (CLARO if i % 2 else BLANCO)
        c.margin_left = c.margin_right = Inches(0.06); c.vertical_anchor = MSO_ANCHOR.MIDDLE
        for p in c.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(12.5 if i else 13); r.font.bold = (i == 0 or j == 0); r.font.name = FUENTE
                r.font.color.rgb = BLANCO if i == 0 else (NAVY if j == 0 else TXT)
caja(sl, 6.1, 5.3, 6.75, 1.5, 'Controlador: PLC Siemens S7-200 CPU 224',
     '2 salidas de tren de pulsos: Q0.0 → base · Q0.1 → carros X e Y (compartida, se elige con los relés K1 y K2)\n'
     'Sin sensor continuo de posición: la posición se conoce contando pulsos', NAR_C, NAR, 15, 13, NAVY)

# ============================================================== 4. P&ID
sl = lamina('1 · Instrumentación', 'P&ID ISA-5.1: cinco lazos, uno por función', 40,
            'Para documentarla levantamos de nuevo los planos con la norma ISA 5.1. Cada función es un lazo con su '
            'número: el 100 es el mando común y el tren de pulsos compartido de los carros, el 101 la base, el 102 el '
            'carro X, el 103 el carro Y y el 104 la garra. En cada lazo los finales de carrera aparecen como interruptores '
            'de posición ZS y el driver con su motor como elemento final ZY. La garra se corrigió: el solenoide va '
            'directo a la salida Q0.7, sin relé intermedio.',
            'El diagrama de tuberías e instrumentación (P&ID) con las zonas coloreadas por lazo. La nomenclatura ISA '
            'permite leer cada eje como un lazo de control: ZS = interruptor de posición (final de carrera o '
            'inductivo), ZY = relé o convertidor de posición (driver + motor), HS = mando manual, XY/XV = solenoide '
            'de la garra. El plano completo (v2.0) está en documentacion/planos_isa.')
img(sl, 'pid_color.png', 0.6, 1.6, 6.0, 5.35, borde=True)
puntos(sl, 6.95, 1.75, 5.95, 5.2, [
    ('Lazo 100 · ', 'mando común: selector HS-100, paro HS-100P y tren de pulsos compartido ZY-100 (Q0.1).'),
    ('Lazo 101 · ', 'base θ: ZY-101 (Q0.0, PTO0), dirección ZY-101D, cero con el inductivo ZS-101.'),
    ('Lazo 102 · ', 'carro X: dirección ZY-102D, relé K1 ZY-102K, finales ZSL/ZSH-102.'),
    ('Lazo 103 · ', 'carro Y: dirección ZY-103D, relé K2 ZY-103K, finales ZSL/ZSH-103.'),
    ('Lazo 104 · ', 'garra: salida XY-104 (Q0.7) → solenoide XV-104, directo, sin relé.'),
    ('Lectura de control: ', 'ningún lazo tiene un transmisor continuo (ZT); solo interruptores ZS → la planta se opera en lazo abierto.')],
    15.5, 9)

# ============================================================== 5. Eléctrico y E/S
sl = lamina('1 · Instrumentación', 'Esquema eléctrico IEC 60617 y mapa de entradas/salidas', 40,
            'El esquema eléctrico, con norma IEC 60617, muestra el detalle que importa para control: la salida Q0.1 '
            'lleva el mismo tren de pulsos a los dos drivers de los carros, y los relés K1 y K2, mandados por Q0.5 y '
            'Q0.6, deciden cuál de los dos lo recibe. Si se cierran ambos, X e Y se mueven a la misma velocidad. Esa '
            'conexión física es la que después aparece en el modelo como una restricción de controlabilidad.',
            'Plano de potencia (izquierda) y la tabla de E/S resumida. La observación clave es el tren de pulsos '
            'compartido: con un solo generador para dos ejes no se pueden mandar velocidades distintas a X e Y al '
            'mismo tiempo. El plano de mando (segunda hoja) muestra la botonera y el selector manual/automático.')
img(sl, 'ele1_color.png', 0.6, 1.6, 6.3, 5.35, borde=True)
filas = [('Entradas', ''), ('I0.0', 'inductivo base = 0'), ('I0.1 / I0.2', 'final X atrás (origen) / adelante'),
         ('I0.3 / I0.4', 'final Y abajo (origen) / arriba'), ('I0.5 · I0.6', 'selector man/auto · paro'), ('I0.7 – I1.5', 'botonera: garra y jog'),
         ('Salidas', ''), ('Q0.0 · Q0.2', 'PUL base (PTO0) · DIR base'), ('Q0.1', 'PUL X/Y compartido (PTO1)'),
         ('Q0.3 · Q0.4', 'DIR X · DIR Y'), ('Q0.5 · Q0.6', 'K1: tren a X · K2: tren a Y'), ('Q0.7', 'solenoide de la garra')]
tb = sl.shapes.add_table(len(filas), 2, Inches(7.2), Inches(1.6), Inches(5.65), Inches(4.4)).table
tb.columns[0].width = Inches(1.65); tb.columns[1].width = Inches(4.0)
for i, (a, b) in enumerate(filas):
    enc = b == ''
    for j, v in enumerate((a, b)):
        c = tb.cell(i, j); c.text = v; c.fill.solid(); c.fill.fore_color.rgb = NAVY if enc else (CLARO if i % 2 else BLANCO)
        c.margin_top = c.margin_bottom = Inches(0.02)
        for p in c.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(12.5); r.font.name = FUENTE; r.font.bold = enc or j == 0
                r.font.color.rgb = BLANCO if enc else (NAVY if j == 0 else TXT)
    if enc: tb.cell(i, 0).merge(tb.cell(i, 1))
for (a, b) in ((8, 1), (10, 1)):
    for r in tb.cell(a, b).text_frame.paragraphs[0].runs: r.font.color.rgb = ROJO; r.font.bold = True
txt(sl, 7.2, 6.2, 5.65, 0.7, 'Un solo tren de pulsos (Q0.1) para dos ejes: K1/K2 eligen el destino.', 14, ROJO, True)

# ============================================================== 6. Estructura de control
sl = lamina('2 · Estructura de control', 'Control de posición en lazo abierto con trenes de pulsos', 60,
            'Con esa instrumentación, el control que hace hoy el PLC es de posición en lazo abierto. No hay una señal '
            'de error entre la referencia y la salida, porque no se mide la salida. El PLC recibe un destino, calcula '
            'cuántos pulsos faltan y los envía en paquetes de 100; la posición es la cuenta de pulsos. Esto es una '
            'ecuación de diferencias de paso fijo, exacta mientras el motor no pierda pasos. La referencia absoluta '
            'la da el homing: los carros van a sus finales de carrera de origen y la cuenta se pone en cero. Las '
            'perturbaciones, como fricción, carga o pérdida de pasos, no se detectan: esa es la principal limitación.',
            'Diagrama de bloques de la planta: referencia → PLC → drivers → motores paso a paso → mecanismo. La '
            'realimentación solo existe de forma discreta (finales de carrera e inductivo), que sirven para el homing y '
            'para cortar el tren de pulsos en los extremos, pero no para corregir la posición durante el movimiento. '
            'La ecuación de diferencias es la que implementa el programa brazo_gemelo del PLC.')
img(sl, 'bloques.png', 0.6, 1.55, 12.2, 2.9, borde=True)
caja(sl, 0.6, 4.6, 6.3, 2.25, 'Ley de control del PLC (cada paquete)',
     'n(k) = n(k−1) + Δn(k)\nΔn(k) = sign(n_ref − n(k−1)) · min(100, |n_ref − n(k−1)|)\n\n'
     'n: posición contada en pulsos · paquetes de 100 pulsos\nX/Y a 4 kHz (ciclo 250 µs) · base a 2,5 kHz (400 µs)', AZ_C, NAVY, 15, 13.5)
puntos(sl, 7.2, 4.6, 5.7, 2.3, [
    ('Referencia: ', 'homing contra los finales de origen (X atrás, Y abajo) y el inductivo de la base.'),
    ('Protección: ', 'los finales cortan el PTO; watchdog si la PC deja de comunicarse.'),
    ('Limitación: ', 'sin error e(k) = r(k) − y(k): la pérdida de pasos no se detecta ni se corrige.')], 14.5, 7)

# ============================================================== 7. Modelo
sl = lamina('3 · Modelo y análisis', 'Modelo identificado: integrador con tiempo muerto por eje', 60,
            'Para modelar automatizamos una prueba escalón: el programa lleva el eje a cero, aplica un escalón de '
            'frecuencia y registra lo que informa el PLC. Lo que sí se puede medir es el tiempo muerto, que es la '
            'latencia de la comunicación más el ciclo del PLC, y la ganancia, que es la velocidad entre la frecuencia. '
            'El modelo de cada eje queda como un integrador con tiempo muerto: posición sobre frecuencia igual a K por '
            'e a la menos t_d s, sobre s, con K igual a 5 micras por pulso. En espacio de estados la matriz A es cero '
            'y la B depende de qué relé está cerrado. Al discretizar con retención de orden cero, G es la identidad y '
            'H es Ts por B. Proponemos 25 milisegundos para un lazo dentro del PLC y unos 155 milisegundos para '
            'supervisión desde la PC, que es lo que tarda una lectura por PPI. La constante de tiempo del motor no se '
            'puede identificar sin un sensor continuo.',
            'La identificación por caja negra se hizo con prueba_escalon.py (laboratorio 4). La figura es una corrida '
            'con el PLC simulado de la app: rampas cuya pendiente es la velocidad v = K·f. El modelo no tiene la forma '
            'K·e^(−t_d s)/(τs+1) porque no hay polo estable observable: el motor paso a paso con su driver se '
            'comporta como un integrador de pulsos. El espacio de estados y la discretización ZOH se calcularon con '
            'espacio_estados_brazo.py/.m (laboratorio 5).')
img(sl, 'escalon.png', 0.6, 1.6, 6.1, 3.3, borde=True)
pie(sl, 'Prueba escalón automatizada (PLC simulado): la pendiente es v = K·f', 0.6, 4.95, 6.1)
caja(sl, 7.0, 1.6, 5.85, 1.2, 'Función de transferencia por eje',
     'S(s) / F(s) = K · e^(−t_d·s) / s     K = 0,005 mm/(Hz·s)\nbase: Θ(s)/F₀(s) = 9,17·10⁻⁵ / s  [rad/pulso]', AZ_C, NAVY, 15, 13.5)
caja(sl, 7.0, 2.95, 5.85, 1.95, 'Espacio de estados  (x = [θ, s_X, s_Y]ᵀ,  u = [f₀, f₁]ᵀ)',
     'ẋ = A·x + B(K1, K2)·u      A = 0\nB(K1,K2) = [ b_θ  0 ; 0  b·K1 ; 0  b·K2 ]\n'
     'ZOH:  G = e^(A·Ts) = I     H = Ts·B', AZ_C, NAVY, 15, 13.5)
caja(sl, 0.6, 5.35, 12.25, 1.5, 'Periodo de muestreo',
     'Ts = 25 ms para un lazo en la interrupción temporizada del PLC  ·  Ts ≈ 155 ms para supervisión desde la PC (una lectura PPI)\n'
     'La regla τ/10 ≤ Ts ≤ τ/4 no se puede aplicar todavía: τ del conjunto motor–carro no es medible sin un sensor continuo', TEAL_C, TEAL, 15, 13.5, TEAL)

# ============================================================== 8. Controlabilidad
sl = lamina('3 · Modelo y análisis', 'Controlabilidad y observabilidad: el hardware limita el control', 45,
            'Con el modelo calculamos las matrices de controlabilidad y observabilidad. Como A es cero, el rango de Mc '
            'es el rango de B. Con un solo relé cerrado, o con los dos, el rango es 2 de 3: el sistema no es '
            'controlable, porque los dos carros comparten el mismo tren de pulsos. Solo conmutando K1 y K2 se alcanzan '
            'todos los estados, que es justamente lo que hace el programa: un tramo común y luego el resto del eje más '
            'largo. En observabilidad, si se midiera la posición el rango sería 3, pero con sensores binarios no hay '
            'una salida lineal: no es observable. Conclusión: con el hardware actual no se puede hacer realimentación '
            'de estados; hace falta un segundo tren de pulsos y un sensor continuo.',
            'Resultados de espacio_estados_brazo.py (salida_espacio_estados.txt, laboratorio 5). Esta lámina conecta '
            'el plano eléctrico (Q0.1 compartida) con la teoría: la restricción física aparece como pérdida de rango '
            'en B. Es el argumento técnico para las mejoras de hardware propuestas al final.')
filas = [('Modo de los relés', 'rango M_C', 'Conclusión'),
         ('K1 cerrado (tren a X)', '2', 'no controlable: Y no recibe pulsos'),
         ('K2 cerrado (tren a Y)', '2', 'no controlable: X no recibe pulsos'),
         ('K1 y K2 cerrados', '2', 'X e Y solo a la misma velocidad'),
         ('ninguno', '1', 'solo la base'),
         ('conmutando K1 ↔ K2', '3', 'todos los estados alcanzables'),
         ('Salida medida', 'rango M_O', ''),
         ('C = J(q₀): posición de la garra', '3', 'observable si se midiera'),
         ('sensores reales (finales, inductivo)', '—', 'binarios: no observable en continuo')]
tb = sl.shapes.add_table(len(filas), 3, Inches(0.6), Inches(1.65), Inches(7.6), Inches(4.6)).table
for j, a in enumerate((3.2, 1.2, 3.2)): tb.columns[j].width = Inches(a)
for i, f in enumerate(filas):
    enc = i in (0, 6)
    for j, v in enumerate(f):
        c = tb.cell(i, j); c.text = v; c.fill.solid()
        c.fill.fore_color.rgb = NAVY if enc else (TEAL_C if i == 5 else (CLARO if i % 2 else BLANCO))
        for p in c.text_frame.paragraphs:
            if j == 1: p.alignment = PP_ALIGN.CENTER
            for r in p.runs:
                r.font.size = Pt(13.5); r.font.name = FUENTE; r.font.bold = enc or j == 1
                r.font.color.rgb = BLANCO if enc else TXT
caja(sl, 8.55, 1.65, 4.3, 2.05, 'M_C = [B  AB  A²B]',
     'con A = 0 → M_C = [B 0 0]\nrango(M_C) = rango(B)\nQ0.1 compartida → B con\ncolumnas dependientes', AZ_C, NAVY, 16, 13.5)
caja(sl, 8.55, 3.9, 4.3, 2.35, 'Conclusión de control',
     'Con el hardware actual NO se puede\nhacer realimentación de estados.\n\nHace falta: 2.º tren de pulsos\n(rango B = 3) y sensor continuo\n(observabilidad).',
     NAR_C, NAR, 16, 13.5, NAVY)
txt(sl, 0.6, 6.4, 12.2, 0.5, 'Calculado con espacio_estados_brazo.py / .m (laboratorio 5).', 12, GRIS, cursiva=True)

# ============================================================== 9. PI discreto
sl = lamina('4 · Diseño de controladores', 'PI discreto por asignación de polos (listo para cuando haya sensor)', 60,
            'Aun así diseñamos los controladores para cuando exista realimentación. Primero un PI discreto por eje, '
            'pensado para la interrupción temporizada del S7-200 a 25 milisegundos. Con la planta b por Ts sobre z menos 1 '
            'y el controlador b0 z más b1 sobre z menos 1, el polinomio característico es de segundo orden. Ubicando un '
            'polo doble en 0,9 salen b0 igual a 1600 y b1 igual a menos 1520 hercios por milímetro. La simulación con '
            'saturación a 5 kilohercios muestra que para escalones pequeños hay un 15 por ciento de sobreimpulso, '
            'que produce el cero del PI, y para escalones grandes el actuador satura, pero no hay sobreimpulso.',
            'Diseño del laboratorio 6 (pi_discreto.py y pi_discreto.m). La ley u(k) = u(k−1) + b0·e(k) + b1·e(k−1) se '
            'ejecutaría en la interrupción temporizada (SMB34 = 25 ms, ATCH al evento 10), guardando e(k−1) y u(k−1) '
            'en memoria V, con u(k) como frecuencia del PTO saturada entre 500 y 5000 Hz. La rutina está escrita '
            '(pi_lazo_flotante.awl) pero no se cargó en el PLC porque no hay sensor de posición.')
img(sl, 'pi.png', 0.6, 1.55, 6.4, 4.7, borde=True)
pie(sl, 'Simulación: polos dobles en 0,9, Ts = 25 ms, saturación a 5 kHz', 0.6, 6.3, 6.4)
caja(sl, 7.3, 1.6, 5.55, 2.05, 'Controlador y diseño',
     'u(k) = u(k−1) + b₀·e(k) + b₁·e(k−1)\nD(z) = (b₀z + b₁)/(z − 1),  G(z) = b·Ts/(z − 1)\n'
     'z² + (b·Ts·b₀ − 2)z + (1 + b·Ts·b₁) = (z − p)²\np = 0,9 → b₀ = 1600 Hz/mm,  b₁ = −1520 Hz/mm', AZ_C, NAVY, 15, 13.5)
filas = [('Escalón', 'Sobreimpulso', 't al 5 %', 't saturado'), ('1 mm', '15,0 %', '0,20 s', '0 %'),
         ('10 mm', '0 %', '0,95 s', '0,3 %'), ('50 mm', '0 %', '2,10 s', '19,4 %')]
tb = sl.shapes.add_table(4, 4, Inches(7.3), Inches(3.85), Inches(5.55), Inches(1.6)).table
for i, f in enumerate(filas):
    for j, v in enumerate(f):
        c = tb.cell(i, j); c.text = v; c.fill.solid(); c.fill.fore_color.rgb = NAVY if i == 0 else (CLARO if i % 2 else BLANCO)
        for p in c.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for r in p.runs: r.font.size = Pt(13.5); r.font.name = FUENTE; r.font.bold = i == 0; r.font.color.rgb = BLANCO if i == 0 else TXT
txt(sl, 7.3, 5.6, 5.55, 1.3, 'Implementación prevista: interrupción temporizada del S7-200 (SMB34 = 25 ms, ATCH evento 10); '
    'u(k) = frecuencia del PTO, saturada a 500–5000 Hz.', 13.5, GRIS)

# ============================================================== 10. LQR
sl = lamina('4 · Diseño de controladores', 'LQR: qué se puede con el hardware actual y con el propuesto', 45,
            'El segundo diseño es un regulador cuadrático óptimo. Con el hardware actual, cualquier ganancia deja un '
            'polo en z igual a 1: el modo diferencia entre los dos carros no es controlable, así que no existe un LQR '
            'de tres ejes. Con un tren de pulsos por eje, que es la mejora propuesta, la ganancia es diagonal y los '
            'polos quedan entre 0,72 y 0,73. Para un carro solo, variando el peso rho, el lazo es de primer orden y '
            'no tiene sobreimpulso: es la ventaja frente al PI. Con rho de 1000 se llega al 5 por ciento en 0,68 segundos.',
            'Resultados de lqr_brazo.py / lqr_brazo.m (laboratorio 7, salida_lqr.txt). Q = diag(1/(1°)², 1/mm², 1/mm²), '
            'R = diag(1/(2500 Hz)²). Con integrador puro y realimentación de estado, el lazo cerrado es de primer '
            'orden, sin sobreimpulso. El LQR no se implementó en el PLC porque requiere medir el estado.')
img(sl, 'lqr.png', 0.6, 1.55, 6.4, 4.7, borde=True)
pie(sl, 'Simulación: un carro, escalón de 10 mm, distintos ρ', 0.6, 6.3, 6.4)
caja(sl, 7.3, 1.6, 5.55, 1.35, 'Hardware actual (Q0.1 compartida)',
     'polos de lazo cerrado = [0,72  0,65  1,00]\nel modo s_X − s_Y no es controlable → no hay LQR de 3 ejes', NAR_C, NAR, 15, 13.5)
caja(sl, 7.3, 3.1, 5.55, 1.35, 'Hardware propuesto (un tren por eje)',
     'K = diag(121 636 · 2 140 · 2 140)  [Hz/rad, Hz/mm]\npolos = [0,72  0,73  0,73]', TEAL_C, TEAL, 15, 13.5, TEAL)
filas = [('ρ [Hz/mm]', 'K [Hz/mm]', 'polo', 't 5 %'), ('200', '197,5', '0,975', '3,00 s'), ('1000', '939,5', '0,883', '0,68 s'),
         ('5000', '3676', '0,541', '0,40 s')]
tb = sl.shapes.add_table(4, 4, Inches(7.3), Inches(4.65), Inches(5.55), Inches(1.5)).table
for i, f in enumerate(filas):
    for j, v in enumerate(f):
        c = tb.cell(i, j); c.text = v; c.fill.solid(); c.fill.fore_color.rgb = NAVY if i == 0 else (CLARO if i % 2 else BLANCO)
        for p in c.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for r in p.runs: r.font.size = Pt(13.5); r.font.name = FUENTE; r.font.bold = i == 0; r.font.color.rgb = BLANCO if i == 0 else TXT
txt(sl, 7.3, 6.25, 5.55, 0.6, 'Sin sobreimpulso en todos los casos (lazo de primer orden).', 13.5, TEAL, True)

# ============================================================== 11. Cinemática
sl = lamina('3 · Modelo y análisis', 'Cinemática: de los carros a la posición de la garra', 30,
            'El último modelo es el geométrico. El brazo es un mecanismo de barras: las posiciones de los carros X e Y '
            'y el ángulo de la base determinan dónde está la garra. Obtuvimos la cinemática directa, la inversa y el '
            'jacobiano, con las cotas del modelo de Inventor del equipo. El espacio de trabajo es una corona entre '
            'unos 400 y 670 milímetros de alcance. Este modelo es el que usa el gemelo digital para dibujar el brazo '
            'y para convertir un punto cartesiano en posiciones de los carros.',
            'Esquema cinemático (izquierda) y el corte r–z del espacio de trabajo (derecha). La cinemática directa '
            'lleva (θ, s_X, s_Y) a la posición del TCP; la inversa resuelve el problema contrario y se verificó que '
            'directa seguida de inversa devuelve la misma posición en toda la grilla. El jacobiano relaciona '
            'velocidades de los carros con velocidades de la garra (manual técnico, capítulo 8).')
img(sl, 'esquema_cinematico.png', 0.6, 1.6, 7.3, 3.45, borde=True)
img(sl, 'espacio_trabajo_rz.png', 8.15, 1.6, 4.7, 3.45, borde=True)
puntos(sl, 0.6, 5.3, 12.2, 1.6, [
    ('Directa e inversa: ', '(θ, s_X, s_Y) ↔ posición del TCP (r, z); directa → inversa devuelve la misma posición en toda la grilla.'),
    ('Cotas: ', 'tomadas del modelo de Inventor del equipo; alcance radial del TCP ≈ 400 – 670 mm.'),
    ('Uso: ', 'el gemelo la usa para dibujar el brazo en 3D y para la pestaña «Cartesiano» (punto alcanzable más cercano).')], 14.5, 5)

# ============================================================== 12. Gemelo: qué es
sl = lamina('5 · Gemelo digital', 'Gemelo digital: una réplica virtual sincronizada con el PLC real', 60,
            'Con todo eso construimos el gemelo digital: una réplica virtual del brazo que está sincronizada con la '
            'planta real. Del lado físico está el PLC con su programa, los drivers y los motores. La aplicación, '
            'escrita en Python, se conecta al puerto del PLC con un cable USB-PPI a 9,6 kilobits por segundo, lee su '
            'memoria, calcula la posición y la muestra en un modelo 3D con la cinemática que acabamos de ver. Funciona '
            'en ambos sentidos: también manda órdenes al PLC. Y alrededor tiene los servicios de supervisión: la base '
            'de datos PostgreSQL con la telemetría, una API REST, una pasarela Modbus TCP y el acceso por la red del '
            'laboratorio para celulares y otras computadoras.',
            'Arquitectura del gemelo. Planta física ↔ protocolo PPI (RS-485, 9,6 kbit/s, cable USB-PPI) ↔ aplicación '
            'en Python (cliente PPI, estimador de posición, PLC simulado, servidor web, registrador de telemetría) ↔ '
            'interfaz web con el modelo 3D (three.js). La misma app corre en Linux y Windows, sin internet. Se eligió '
            'una app propia en lugar de Simulink porque, además de simular, debía conectarse al PLC y servir de '
            'interfaz de operación.')
caja(sl, 0.6, 1.75, 3.3, 3.0, 'Planta física',
     'PLC S7-200 CPU 224\nprograma brazo_gemelo\n(memoria V: órdenes y estado)\n\ndrivers JMC + motores\nfinales e inductivo', NAR_C, NAR, 17, 13.5)
caja(sl, 5.0, 1.75, 3.6, 3.0, 'App del gemelo (Python)',
     'cliente PPI\nestimador de posición\nPLC simulado (sin brazo)\nservidor web local y HTTPS\nregistrador de telemetría', TEAL_C, TEAL, 17, 13.5, TEAL)
caja(sl, 9.6, 1.75, 3.25, 3.0, 'Interfaz',
     'modelo 3D (three.js)\ncon la cinemática\n\npaneles: articular,\ncartesiano, secuencias,\nconexión, dashboard', AZ_C, NAVY, 17, 13.5)
flecha(sl, 3.95, 3.25, 4.95, 3.25, NAVY, True, 2.5); txt(sl, 3.75, 2.5, 1.4, 0.7, 'PPI\n9,6 kbit/s', 12, NAVY, True, PP_ALIGN.CENTER)
txt(sl, 3.75, 3.35, 1.4, 0.7, 'estado ↔\nórdenes', 11, GRIS, alin=PP_ALIGN.CENTER)
flecha(sl, 8.65, 3.25, 9.55, 3.25, NAVY, True, 2.5); txt(sl, 8.5, 2.55, 1.2, 0.6, 'HTTP', 12, NAVY, True, PP_ALIGN.CENTER)
servicios = [('PostgreSQL', 'telemetría 1 muestra/s,\nalarmas, órdenes'), ('API REST', '/api/v1 con token\n(operador / observador)'),
             ('Modbus TCP', 'registros 40001–40015\nsolo lectura'), ('Red del laboratorio', 'HTTPS :8443, celulares\ny PC con roles')]
for i, (t, c) in enumerate(servicios):
    x = 0.6 + i * 3.1
    caja(sl, x, 5.35, 2.95, 1.45, t, c, CLARO, GRIS, 15, 12.5)
    flecha(sl, x + 1.475, 5.3, 6.8 if i < 2 else 6.8, 4.8, GRIS, False, 1.5)

# ============================================================== 13. Cómo funciona
sl = lamina('5 · Gemelo digital', 'Cómo funciona: el ciclo de lectura, cálculo y mando', 60,
            'El funcionamiento es un ciclo. Primero la app lee del PLC las entradas, las salidas y la memoria de '
            'estado; una lectura tarda unos 155 milisegundos. Segundo, calcula la posición: con nuestro programa '
            'brazo_gemelo el PLC cuenta los pulsos y la posición es exacta al pulso; con el programa original, que no '
            'cuenta, la app la estima integrando la frecuencia de los trenes y la corrige en los finales de carrera, '
            'con un error máximo de 1,35 milímetros. Tercero, aplica la cinemática y mueve el modelo 3D. Cuarto, si el '
            'operador da una orden, la escribe en la memoria V: homing, mover, paro o garra, con un número de secuencia '
            'y un latido; si la PC deja de responder, el watchdog del PLC detiene el brazo. La app tiene tres modos: '
            'simulación, operación local y operación por red.',
            'El ciclo del gemelo. La interfaz PC–PLC es un bloque de memoria V: VB1100 (orden), VB1101 (secuencia), '
            'VW1102 (latido), VD1104–VD1112 (destino en pulsos) y, de vuelta, VB1120–VB1141 (estado, posición, '
            'entradas, salidas y firma del programa). El estimador se validó contra el programa original con '
            'pruebas_estimador.py (error máximo 1,35 mm en 170 mm, 99,2 %).')
pasos = [('1', 'Leer', 'entradas, salidas y memoria\nde estado del PLC por PPI\n(≈ 155 ms por lectura)'),
         ('2', 'Calcular', 'posición exacta (cuenta de\npulsos) o estimada con f·dt\ny corregida en los finales'),
         ('3', 'Mostrar', 'cinemática directa →\nmodelo 3D, señales,\nalarmas y telemetría'),
         ('4', 'Mandar', 'orden en VB1100 con\nsecuencia y latido;\nwatchdog en el PLC')]
for i, (k, t, c) in enumerate(pasos):
    x = 0.6 + i * 3.13
    s = caja(sl, x, 1.7, 2.8, 2.25, t, c, TEAL_C if i % 2 == 0 else AZ_C, TEAL if i % 2 == 0 else NAVY, 18, 13.5)
    o = rect(sl, x - 0.12, 1.58, 0.5, 0.5, NAR, forma=MSO_SHAPE.OVAL); p = o.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = k; r.font.bold = True; r.font.size = Pt(15); r.font.color.rgb = BLANCO; r.font.name = FUENTE
    if i < 3: flecha(sl, x + 2.83, 2.82, x + 3.1, 2.82, NAR, False, 2.5)
txt(sl, 0.6, 4.1, 12.2, 0.4, '↺  el ciclo se repite mientras la app está abierta', 13, GRIS, cursiva=True, alin=PP_ALIGN.CENTER)
modos = [('Simulación', 'PLC simulado dentro de la app:\nmismo programa, tiempos y errores.\nPracticar sin brazo ni cable.'),
         ('Operación local', 'sigue al brazo real y lo manda\ndesde la PC del laboratorio.'),
         ('Operación por red', 'además, celulares y PC de la red\nentran por HTTPS con usuario\no como observadores libres.')]
for i, (t, c) in enumerate(modos):
    caja(sl, 0.6 + i * 4.15, 4.6, 3.95, 1.55, t, c, CLARO, GRIS, 16, 13)
txt(sl, 0.6, 6.3, 12.25, 0.6, 'Seguridad: un solo operador tiene el mando · el paro siempre está disponible · watchdog en el PLC · '
    'la seta de emergencia física manda sobre todo.', 13.5, ROJO, True)

# ============================================================== 14. Observadores libres
sl = lamina('5 · Gemelo digital', 'Acceso por red: operadores, observadores y observadores libres', 50,
            'Para clases y demostraciones agregamos los observadores libres. En el modo de operación por red, el menú '
            'tiene una casilla nueva: «Observadores libres». Al marcarla, el código QR de la pantalla lleva '
            'directamente a la vista del brazo, sin usuario ni contraseña. Cada persona entra como visita-1, visita-2, '
            'etcétera, y ve el brazo en vivo en su celular. Es solo lectura: el servidor rechaza cualquier orden o '
            'pedido de mando de una visita, y al desmarcar la casilla se cierran todas esas sesiones. Para mandar el '
            'brazo sigue haciendo falta un usuario operador con contraseña.',
            'Roles del acceso por red: operador (usuario y contraseña; ve y manda, uno a la vez), observador con '
            'usuario (solo ve) y, desde esta versión, observador libre (sin contraseña, solo ve). La casilla está en '
            'el menú, se puede activar también con --observadores-libres, y viene apagada al abrir la app. El '
            'servidor valida el rol en cada petición: una visita recibe 403 si intenta mover o tomar el mando. Las '
            'contraseñas de los usuarios se guardan con PBKDF2-SHA256 y la conexión va cifrada con un certificado propio.')
img(sl, 'menu_red_card.png', 0.6, 1.6, 5.4, 1.95, borde=True)
img(sl, 'menu_qr.png', 6.15, 1.6, 3.05, 1.95, borde=True)
img(sl, 'observador_celular.png', 9.55, 1.6, 3.3, 5.3, borde=True)
filas = [('Rol', 'Cómo entra', 'Qué puede hacer'),
         ('Operador', 'usuario + contraseña', 'ver, mandar (uno a la vez) y paro'),
         ('Observador', 'usuario + contraseña', 'ver en vivo y el dashboard'),
         ('Observador libre', 'QR / botón, sin contraseña', 'solo ver · sale como visita-N')]
tb = sl.shapes.add_table(4, 3, Inches(0.6), Inches(3.75), Inches(8.6), Inches(1.65)).table
for j, a in enumerate((2.1, 2.9, 3.6)): tb.columns[j].width = Inches(a)
for i, f in enumerate(filas):
    for j, v in enumerate(f):
        c = tb.cell(i, j); c.text = v; c.fill.solid()
        c.fill.fore_color.rgb = NAVY if i == 0 else (NAR_C if i == 3 else (CLARO if i % 2 else BLANCO))
        for p in c.text_frame.paragraphs:
            for r in p.runs: r.font.size = Pt(13.5); r.font.name = FUENTE; r.font.bold = i == 0 or j == 0; r.font.color.rgb = BLANCO if i == 0 else TXT
puntos(sl, 0.6, 5.6, 8.6, 1.4, [
    ('Activar: ', 'menú → Operación por red → casilla «Observadores libres» → el QR apunta a /libre.'),
    ('Seguro por diseño: ', 'el servidor rechaza órdenes y mando de una visita (403); al desmarcar, se cierran sus sesiones.')], 13.5, 4)

# ============================================================== 15. Supervisión
sl = lamina('5 · Gemelo digital', 'Supervisión: telemetría, indicadores e integración industrial', 30,
            'Todo lo que pasa queda registrado. La app guarda una muestra por segundo de cada variable en PostgreSQL, '
            'además de las alarmas, las órdenes y los ingresos. El dashboard muestra indicadores, como la eficiencia '
            'homeostática, y las series de tiempo de cada eje. Otros sistemas pueden leer esos datos por la API REST '
            'con token o por Modbus TCP, como lo haría un SCADA. Las pruebas de control de acceso por roles pasaron '
            '18 de 18.',
            'El dashboard (botón «Dashboard» de la app) lee de PostgreSQL a través de la API. La base tiene triggers '
            'que rechazan datos fuera de rango y generan alarmas (laboratorio 5). La pasarela Modbus TCP publica el '
            'estado en los registros 40001–40015, solo lectura (laboratorio 8). El certificado RBAC del laboratorio 7 '
            'documenta las 18 pruebas de permisos por rol.')
img(sl, 'dashboard.jpg', 0.6, 1.6, 6.9, 5.3, borde=True)
puntos(sl, 7.85, 1.75, 5.0, 5.2, [
    ('Telemetría: ', 'PostgreSQL, 1 muestra/s por variable, cambios de señales, alarmas, órdenes y sesiones.'),
    ('Dashboard: ', 'eficiencia homeostática, horas de operación, series de tiempo por eje.'),
    ('API REST: ', '/api/v1 con token Bearer; el observador solo lee.'),
    ('Modbus TCP: ', 'puerto 5020, registros 40001–40015, solo lectura.'),
    ('Validación: ', 'triggers rechazan datos fuera de rango; RBAC 18/18 pruebas.')], 15, 9)

# ============================================================== 16. Demostración
sl = lamina('6 · Demostración en vivo', 'Demostración: la app del gemelo en funcionamiento', 120,
            'Ahora pasamos a la demostración. Abrimos la app: aparece el menú con los tres modos. [Paso 1] Entramos en '
            'simulación, hacemos homing y movemos los ejes desde la pestaña articular; luego en cartesiano elegimos un '
            'punto y el gemelo propone el alcanzable más cercano. [Paso 2] Volvemos al menú, elegimos operación por red '
            'y marcamos observadores libres. [Paso 3] Les pedimos que escaneen el QR con el celular conectado a la red '
            'del laboratorio: van a entrar como visitas y verán el brazo moverse en vivo. Si alguien toca un botón de '
            'mando, el servidor lo rechaza. [Paso 4] Mostramos el dashboard con la telemetría. Si el brazo y el cable '
            'están conectados, hacemos lo mismo con la planta real; si no, con la casilla «sin brazo» usamos el PLC '
            'simulado.',
            'Guion de la demostración (≈ 2 min). Antes de la presentación: abrir la app, comprobar que la PC y los '
            'celulares están en la misma red Wi-Fi y, si se usa el brazo real, que el cable USB-PPI está conectado y '
            'alguien está junto a la seta de emergencia. Plan B: casilla «Sin brazo: usar el PLC simulado».')
pasos = [('1', 'Simulación', 'Menú → Simulación → Homing → mover en «Articular» y «Cartesiano» → «Espacio de trabajo».', '40 s'),
         ('2', 'Red + observadores libres', 'Menú → Operación por red → marcar «Observadores libres» (y «Sin brazo» si no hay planta).', '20 s'),
         ('3', 'Público con el celular', 'Escanear el QR → entran como visita-N y ven el brazo en vivo; un intento de mando se rechaza.', '40 s'),
         ('4', 'Supervisión', 'Botón «Dashboard»: indicadores y series de tiempo del movimiento recién hecho.', '20 s')]
for i, (k, t, c, tt) in enumerate(pasos):
    y = 1.65 + i * 1.08
    o = rect(sl, 0.6, y + 0.12, 0.62, 0.62, NAR, forma=MSO_SHAPE.OVAL); p = o.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = k; r.font.bold = True; r.font.size = Pt(18); r.font.color.rgb = BLANCO; r.font.name = FUENTE
    txt(sl, 1.4, y, 5.4, 0.4, t + f'   ·  {tt}', 17, NAVY, True)
    txt(sl, 1.4, y + 0.38, 5.6, 0.7, c, 13.5, TXT)
img(sl, 'gemelo_red.png', 7.2, 1.65, 5.65, 3.4, borde=True)
caja(sl, 7.2, 5.3, 5.65, 1.55, 'Antes de empezar',
     'PC y celulares en la misma red Wi-Fi · cable USB-PPI conectado\nalguien junto a la seta de emergencia\nPlan B: «Sin brazo: usar el PLC simulado»', NAR_C, NAR, 15, 13)

# ============================================================== 17. Conclusiones
sl = lamina('7 · Cierre', 'Resultados, limitaciones y trabajo futuro', 45,
            'Para cerrar. Logramos documentar la planta con normas, modelarla, analizar sus propiedades estructurales y '
            'diseñar dos controladores, y construimos un gemelo digital que funciona con la planta real y en '
            'simulación, con supervisión y acceso por red. La principal conclusión de control es que el hardware '
            'actual limita la planta a lazo abierto: no hay sensor continuo y dos ejes comparten un tren de pulsos. Las '
            'mejoras concretas son un encoder o regla lineal leído con el contador rápido del PLC, para cerrar el lazo '
            'con el PI que ya está diseñado, y un segundo generador de pulsos, para el LQR de tres ejes.',
            'Resumen de lo logrado, de lo que limita el control y de los pasos siguientes. Las mejoras propuestas '
            'salen directamente del análisis de controlabilidad y observabilidad: un sensor continuo hace la planta '
            'observable y un segundo tren de pulsos hace que B tenga rango 3.')
cols = [('Logrado', TEAL_C, TEAL, ['Planos v2.0 ISA-5.1 / IEC 60617', 'Modelo identificado y espacio de estados',
                                   'Controlabilidad y observabilidad', 'PI discreto y LQR diseñados y simulados',
                                   'Gemelo digital con PLC real y simulado', 'Red con roles y observadores libres',
                                   'Telemetría, dashboard, API y Modbus']),
        ('Limitaciones', NAR_C, NAR, ['Sin sensor continuo de posición: lazo abierto', 'Un tren de pulsos para X e Y',
                                       'τ del motor no identificable', 'Fidelidad medida contra la cuenta de pulsos, falta el calibre']),
        ('Trabajo futuro', AZ_C, NAVY, ['Encoder o regla lineal con el contador rápido (HSC)', 'Cerrar el lazo con el PI en interrupción',
                                         'Segundo PTO o módulo de posicionamiento → LQR de 3 ejes', 'Medición con calibre del índice de fidelidad'])]
for i, (t, fondo, borde, its) in enumerate(cols):
    x = 0.6 + i * 4.15
    rect(sl, x, 1.65, 3.95, 4.6, fondo, borde, MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(sl, x + 0.2, 1.8, 3.6, 0.45, t, 19, borde if borde != NAVY else NAVY, True)
    puntos(sl, x + 0.2, 2.35, 3.6, 3.8, its, 15, 9, col_v=borde)
txt(sl, 0.6, 6.4, 12.25, 0.55, 'El análisis de control dice exactamente qué hardware falta: un sensor continuo (observabilidad) y un segundo tren de pulsos (controlabilidad).', 14.5, NAVY, True, PP_ALIGN.CENTER)

# ============================================================== 18. Preguntas
sl = prs.slides.add_slide(VACIA)
sl.background.fill.solid(); sl.background.fill.fore_color.rgb = NAVY
txt(sl, 0.8, 2.0, 7.5, 1.2, 'Gracias', 54, BLANCO, True)
txt(sl, 0.8, 3.15, 7.5, 0.6, '¿Preguntas?', 28, NAR, True)
rect(sl, 0.82, 3.95, 1.3, 0.06, NAR)
txt(sl, 0.8, 4.2, 7.5, 1.6, 'Documentación, planos, informes y la app:\nbrazo-4gdl.pages.dev\ngithub.com/GabAndGom/Brazo-de-4-grados-de-libertad', 16, RGBColor(0xDD, 0xE6, 0xEE))
rect(sl, 8.95, 1.6, 3.6, 3.6, BLANCO, forma=MSO_SHAPE.ROUNDED_RECTANGLE)
img(sl, 'qr_pagina.png', 9.1, 1.75, 3.3, 3.3)
txt(sl, 8.95, 5.35, 3.6, 0.4, 'Página del proyecto', 14, RGBColor(0xB8, 0xC7, 0xD6), alin=PP_ALIGN.CENTER)
notas(sl, 18, 'Preguntas', 10, 'Gracias por su atención. En la página del proyecto, que pueden abrir con este QR, están los '
      'planos, los informes, los manuales y la app. Quedamos atentos a sus preguntas.')
DATOS.append({'n': 18, 'titulo': 'Gracias · Preguntas', 'seccion': 'Cierre', 'segundos': 10,
              'guion': sl.notes_slide.notes_text_frame.text.split('\n\n', 1)[1],
              'explicacion': 'Cierre con el enlace a la página pública del proyecto y al repositorio.'})

DATOS.sort(key=lambda d: d['n'])
salida = os.path.join(D, 'presentacion_control_gemelo_brazo.pptx'); prs.save(salida)
json.dump({'total_s': TOTAL[0], 'laminas': DATOS}, open(os.path.join(D, 'datos_laminas.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(salida, len(prs.slides), 'láminas', f'{TOTAL[0] // 60}:{TOTAL[0] % 60:02d}')
