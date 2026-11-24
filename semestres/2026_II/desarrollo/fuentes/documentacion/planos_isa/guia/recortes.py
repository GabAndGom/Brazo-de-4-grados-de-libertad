#!/usr/bin/env python3
"""Recortes ampliados de los planos v2.0 para la guía de lectura (guia_lectura_planos.tex).

Rasteriza los PDF públicos a 300 ppp y guarda en img/ las zonas que explica la guía; algunas llevan
recuadros de color que marcan los lazos o las partes que se comentan en el texto.
Las cajas están en píxeles de una vista a 110 ppp (A3 apaisado = 1820 x 1287) y se escalan solas.
"""
import os
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
PLANOS = os.path.normpath(os.path.join(AQUI, '../../../../../documentacion/planos_isa'))
PDF = {'pid': 'pid/brazo_pid_v2.pdf', 'ele': 'electrico/brazo_electrico_v2.pdf'}
PPP, BASE = 300, 110
K = PPP / BASE

COLORES = {'teal': (11, 122, 115), 'naranja': (194, 98, 12), 'morado': (120, 60, 160), 'azul': (0, 103, 184),
           'rojo': (192, 57, 43), 'verde': (30, 120, 70)}

# nombre: (plano, página, caja, [(caja_marca, color, etiqueta), ...])
RECORTES = {
    'pid_completo': ('pid', 1, (0, 0, 1820, 1287), [
        ((40, 150, 960, 370), 'azul', 'Operador (botonera) y PC'),
        ((150, 390, 965, 528), 'morado', 'PLC: funciones compartidas'),
        ((150, 600, 345, 1065), 'naranja', 'Lazo 101 base'),
        ((350, 540, 600, 1065), 'teal', 'Lazo 102 X'),
        ((600, 540, 845, 1065), 'verde', 'Lazo 103 Y'),
        ((850, 600, 960, 1065), 'rojo', 'Lazo 104 garra'),
        ((80, 1065, 965, 1195), 'grisos', 'Planta')]),
    'pid_leyenda': ('pid', 1, (1065, 75, 1460, 625), []),
    'pid_operador': ('pid', 1, (40, 95, 965, 335), []),
    'pid_plc': ('pid', 1, (150, 385, 970, 530), []),
    'pid_base': ('pid', 1, (100, 520, 345, 1075), []),
    'pid_xy': ('pid', 1, (345, 520, 850, 1075), [((560, 555, 630, 590), 'rojo', '')]),
    'pid_garra': ('pid', 1, (800, 215, 965, 1075), []),
    'pid_notas': ('pid', 1, (1065, 640, 1460, 760), []),
    'pid_revision': ('pid', 1, (995, 840, 1775, 975), []),
    'ele1_completo': ('ele', 1, (0, 0, 1820, 1287), [
        ((45, 60, 420, 640), 'rojo', 'Alimentación'),
        ((90, 535, 1775, 625), 'azul', 'Barras 24 V / 0 V'),
        ((245, 590, 700, 840), 'verde', '-A1 eje Y'),
        ((680, 590, 1130, 840), 'teal', '-A2 eje X'),
        ((1110, 590, 1600, 840), 'naranja', '-A3 base'),
        ((120, 895, 500, 1015), 'morado', 'DIP')]),
    'ele1_alimentacion': ('ele', 1, (45, 65, 420, 625), []),
    'ele1_barras': ('ele', 1, (90, 520, 1775, 625), []),
    'ele1_driver': ('ele', 1, (240, 590, 790, 840), []),
    'ele1_drivers': ('ele', 1, (240, 590, 1600, 840), []),
    'ele1_dip': ('ele', 1, (120, 895, 500, 1015), []),
    'ele1_revision': ('ele', 1, (995, 855, 1775, 975), []),
    'ele2_completo': ('ele', 2, (0, 0, 1820, 1287), [
        ((80, 130, 1000, 445), 'naranja', 'Salidas'),
        ((130, 415, 1000, 640), 'morado', 'PLC -A4'),
        ((80, 645, 1000, 985), 'azul', 'Entradas'),
        ((1040, 490, 1260, 745), 'rojo', 'Garra'),
        ((1130, 60, 1770, 490), 'teal', 'Tabla E/S')]),
    'ele2_salidas': ('ele', 2, (80, 130, 1000, 445), []),
    'ele2_pulsos': ('ele', 2, (260, 170, 440, 440), []),
    'ele2_reles': ('ele', 2, (590, 140, 1000, 440), []),
    'ele2_plc': ('ele', 2, (125, 410, 1000, 640), []),
    'ele2_garra': ('ele', 2, (1040, 490, 1260, 745), []),
    'ele2_entradas': ('ele', 2, (80, 610, 1000, 985), []),
    'ele2_sensor': ('ele', 2, (80, 640, 470, 980), []),
    'ele2_paralelos': ('ele', 2, (540, 640, 760, 980), []),
    'ele2_tabla': ('ele', 2, (1130, 60, 1770, 490), []),
    'ele2_notas': ('ele', 2, (120, 985, 600, 1035), []),
    'ele2_revision': ('ele', 2, (995, 855, 1775, 975), []),
}
COLORES['grisos'] = (90, 90, 90)


def fuente(tam):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',):
        if os.path.exists(f):
            return ImageFont.truetype(f, tam)
    return ImageFont.load_default()


def main():
    os.makedirs(os.path.join(AQUI, 'img'), exist_ok=True)
    paginas = {}
    with tempfile.TemporaryDirectory() as tmp:
        for clave, rel in PDF.items():
            subprocess.run(['pdftoppm', '-r', str(PPP), '-png', os.path.join(PLANOS, rel), os.path.join(tmp, clave)],
                           check=True)
            for n in (1, 2):
                ruta = os.path.join(tmp, f'{clave}-{n}.png')
                if os.path.exists(ruta):
                    paginas[(clave, n)] = Image.open(ruta).convert('RGB')
        for nombre, (plano, pag, caja, marcas) in RECORTES.items():
            im = paginas[(plano, pag)].copy()
            d = ImageDraw.Draw(im, 'RGBA')
            for (x0, y0, x1, y1), col, etq in marcas:
                c = COLORES[col]
                b = [int(v * K) for v in (x0, y0, x1, y1)]
                d.rectangle(b, outline=c + (255,), width=9, fill=c + (22,))
                if etq:
                    f = fuente(46)
                    w = d.textlength(etq, font=f)
                    d.rectangle([b[0], b[1] - 62, b[0] + w + 24, b[1]], fill=c + (235,))
                    d.text((b[0] + 12, b[1] - 58), etq, font=f, fill=(255, 255, 255))
            recorte = im.crop(tuple(int(v * K) for v in caja))
            if caja[2] - caja[0] > 1500:   # planos completos: más livianos
                recorte = recorte.resize((recorte.width // 2, recorte.height // 2), Image.LANCZOS)
            recorte.save(os.path.join(AQUI, 'img', nombre + '.png'), optimize=True)
            print(nombre, recorte.size)


if __name__ == '__main__':
    main()
