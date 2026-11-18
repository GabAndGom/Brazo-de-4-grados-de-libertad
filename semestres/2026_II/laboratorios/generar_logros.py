#!/usr/bin/env python3
"""Genera, desde logros_datos.py:

    objetivos_laboratorios.xlsx              objetivos de cada guía, lo alcanzado y qué es
    labNN_*/logros_labNN.tex (y .pdf)        logros del laboratorio frente a sus objetivos y trabajo del docente

    python3 generar_logros.py            (desde esta carpeta; requiere openpyxl y pdflatex)

El porcentaje de las tareas del docente se toma de evaluacion_tareas_docente.xlsx, que edita el equipo.
"""
import os
import re
import subprocess

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.formatting.rule import CellIsRule

from logros_datos import FECHA, LABS

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = 'https://github.com/GabAndGom/Brazo-de-4-grados-de-libertad'


def tareas_docente():
    """{Nº: (porcentaje o texto, lo que falta)} del Excel de tareas del docente."""
    ws = openpyxl.load_workbook(os.path.join(AQUI, 'evaluacion_tareas_docente.xlsx')).active
    out = {}
    for fila in ws.iter_rows(min_row=5, values_only=True):
        if isinstance(fila[0], int):
            out[fila[0]] = (fila[5], fila[4])
    return out


# ------------------------------------------------------------------------------------------- texto plano y LaTeX
def plano(s):
    return s.replace('`', '').replace('**', '')


UNICODE = {'θ': r'$\theta$', 'τ': r'$\tau$', 'η': r'$\eta$', 'ρ': r'$\rho$', 'Δ': r'$\Delta$', '≤': r'$\le$',
           '≥': r'$\ge$', '≈': r'$\approx$', '×': r'$\times$', '·': r'$\cdot$', '→': r'$\to$', '↔': r'$\leftrightarrow$',
           '−': '-', 'ẋ': r'$\dot{x}$', '±': r'$\pm$'}


def esc(s):
    s = s.replace('\\', r'\textbackslash{}')
    for a, b in (('&', r'\&'), ('%', r'\%'), ('_', r'\_'), ('#', r'\#'), ('{', r'\{'), ('}', r'\}'), ('^', r'\^{}'),
                 ('~', r'\~{}')):
        s = s.replace(a, b)
    for a, b in UNICODE.items():
        s = s.replace(a, b)
    return s


def tex(s):
    """Texto con `código`, **negrita** y enlaces http a LaTeX."""
    partes = re.split(r'(`[^`]+`|https?://\S+)', s)
    out = []
    for p in partes:
        if p.startswith('`'):
            out.append(r'\codigo{' + esc(p[1:-1]) + '}')
        elif p.startswith('http'):
            fin = ''
            while p and p[-1] in '.,;)':
                fin = p[-1] + fin
                p = p[:-1]
            out.append(r'\url{' + p + '}' + esc(fin))
        else:
            out.append(re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', esc(p)))
    return ''.join(out)


def ruta(e):
    if e.startswith('http'):
        return r'\url{' + e + '}'
    return r'\codigo{' + esc(e) + '}'


def estado(p):
    if not isinstance(p, (int, float)):
        return r'\textit{no aplica}', '—'
    pct = f'{round(p * 100)}\\%'
    if p >= 1:
        return r'\cumple', pct
    if p <= 0:
        return r'\falta', pct
    return r'\parcial', pct


# ----------------------------------------------------------------------------------------------------- Excel
def excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Objetivos por laboratorio'
    azul, gris = PatternFill('solid', fgColor='1F3864'), PatternFill('solid', fgColor='EDEDED')
    fino = Side(style='thin', color='A6A6A6')
    borde = Border(left=fino, right=fino, top=fino, bottom=fino)
    ws['A1'] = 'Objetivos de los laboratorios y alcance logrado'
    ws['A1'].font = Font(bold=True, size=14, color='1F3864')
    ws['A2'] = (f'Brazo XK-JS1-1 (4 GDL) · ETN-902 / ETN-1034 / ETN-1000 · II/2026 · estado al {FECHA}. '
                'Objetivos tomados de la sección 1 de cada guía. El porcentaje (azul) es editable.')
    ws['A2'].font = Font(italic=True, size=9, color='595959')
    cab = ['Nº', 'Lab.', 'Mención', 'Objetivo (según la guía)', 'Lo alcanzado hasta el momento',
           'Qué es (explicación)', 'Evidencia en el repositorio', 'Lo que falta', '% alcanzado']
    anchos = [5, 6, 13, 34, 62, 50, 36, 36, 11]
    for i, (c, w) in enumerate(zip(cab, anchos), 1):
        celda = ws.cell(row=4, column=i, value=c)
        celda.font, celda.fill, celda.border = Font(bold=True, color='FFFFFF'), azul, borde
        celda.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    fila, n = 5, 0
    for lab in LABS:
        ws.cell(row=fila, column=1, value=f'Laboratorio {lab["n"]}: {lab["titulo"]} · entrega {lab["entrega"]} · '
                                          f'{lab["estado"]}')
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=len(cab))
        ws.cell(row=fila, column=1).font = Font(bold=True, color='1F3864')
        ws.cell(row=fila, column=1).fill = gris
        fila += 1
        for o in lab['objetivos']:
            n += 1
            vals = [n, lab['n'], o['mencion'], f'{o["nombre"]}: {plano(o["guia"])}',
                    '\n'.join('• ' + plano(x) for x in o['logrado']), plano(o['que_es']),
                    '\n'.join(o['evidencia']), plano(o['falta']), o['pct']]
            for i, v in enumerate(vals, 1):
                c = ws.cell(row=fila, column=i, value=v)
                c.border = borde
                c.alignment = Alignment(vertical='top', wrap_text=True, horizontal='center' if i in (1, 2, 9) else None)
                c.font = Font(size=9, bold=(i == 4))
            ws.cell(row=fila, column=9).number_format = '0%'
            ws.cell(row=fila, column=9).font = Font(size=10, bold=True, color='0000FF')
            alto = max(len(vals[4]) / 62, len(vals[5]) / 50, len(vals[3]) / 34) * 13 + 6 * len(o['logrado'])
            ws.row_dimensions[fila].height = min(409, max(45, alto))
            fila += 1
    rango = f'I5:I{fila - 1}'
    ws.conditional_formatting.add(rango, CellIsRule(operator='greaterThanOrEqual', formula=['1'],
                                                    fill=PatternFill('solid', fgColor='C6EFCE')))
    ws.conditional_formatting.add(rango, CellIsRule(operator='between', formula=['0.5', '0.9999'],
                                                    fill=PatternFill('solid', fgColor='FFEB9C')))
    ws.conditional_formatting.add(rango, CellIsRule(operator='lessThan', formula=['0.5'],
                                                    fill=PatternFill('solid', fgColor='FFC7CE')))
    ws.freeze_panes = 'D5'
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = '4:4'
    wb.save(os.path.join(AQUI, 'objetivos_laboratorios.xlsx'))
    print('objetivos_laboratorios.xlsx:', n, 'objetivos')


# ------------------------------------------------------------------------------------------------- documentos
def documento(lab, docente):
    L = []
    w = L.append
    w(f'% Logros del laboratorio {lab["n"]} frente a sus objetivos y trabajo del docente.')
    w('% Generado por ../generar_logros.py desde ../logros_datos.py: editar los datos y regenerar.')
    w(r'\documentclass[a4paper,11pt]{article}')
    w(r'\input{../informe_comun}')
    w(r'\renewcommand{\tipodoc}{Logros del Laboratorio Integrado}')
    w(r'\renewcommand{\tipocab}{Logros del laboratorio}')
    w(r'\begin{document}')
    w(rf'\portada{{{lab["n"]}}}{{{tex(lab["titulo"])}}}{{{lab["inicio"]}}}{{{lab["entrega"]}}}{{{lab["semanas"]}}}')
    w(r'\tableofcontents')
    w(r'\newpage')
    w(rf'\nota{{\textbf{{Estado al {FECHA}.}} {tex(lab["estado"])} {tex(lab["fase"])}. Este documento explica, objetivo por objetivo, '
      r'qué pide la guía, qué logró la escuadra, qué es cada cosa y dónde está la evidencia; después explica el '
      r'trabajo del docente: qué debía revisar en cada hito y qué tiene preparado la escuadra para esa revisión.}')

    w(r'\section{Resumen}')
    w(r'\begin{center}\small\begin{tabularx}{\linewidth}{c >{\raggedright}p{2.4cm} >{\raggedright}X c c}')
    w(r'\toprule \textbf{Nº} & \textbf{Mención} & \textbf{Objetivo} & \textbf{Estado} & \textbf{\%}\\ \midrule')
    for i, o in enumerate(lab['objetivos'], 1):
        e, p = estado(o['pct'])
        w(rf'{i} & {o["mencion"]} & {tex(o["nombre"])} & {e} & {p}\\')
    w(r'\bottomrule\end{tabularx}\end{center}')
    w(r'El porcentaje mide cuánto del objetivo está hecho y comprobado en la planta o en el repositorio; '
      r'no cuenta lo que solo está planificado.')

    w(r'\section{Logros respecto de los objetivos}')
    for menc in dict.fromkeys(o['mencion'] for o in lab['objetivos']):
        nombre = 'Control Automático' if menc.startswith('ETN-902') else 'Sistemas Computacionales'
        w(rf'\subsection{{Mención {nombre} ({menc})}}')
        for o in (x for x in lab['objetivos'] if x['mencion'] == menc):
            e, p = estado(o['pct'])
            w(rf'\subsubsection{{{tex(o["nombre"])}}}')
            w(rf'\paragraph{{Qué pide la guía.}} {tex(o["guia"])}')
            w(r'\paragraph{Qué se logró.}')
            w(r'\begin{itemize}')
            for x in o['logrado']:
                w(rf'\item {tex(x)}')
            w(r'\end{itemize}')
            w(rf'\paragraph{{Qué es y por qué importa.}} {tex(o["que_es"])}')
            w(r'\paragraph{Evidencia.}')
            w(r'\begin{itemize}\small')
            for x in o['evidencia']:
                w(rf'\item {ruta(x)}')
            w(r'\end{itemize}')
            falta = 'nada para este objetivo.' if o['falta'] == '—' else tex(o['falta'])
            w(rf'\paragraph{{Lo que falta.}} {falta}')
            w(rf'\paragraph{{Estado:}} {e}~({p}).')

    w(r'\section{Trabajo del docente}')
    w(r'La guía asigna al docente el papel de auditor: en cada hito revisa el trabajo de la escuadra y decide si '
      r'cumple antes de pasar a la etapa siguiente. Para cada tarea se explica qué debía revisar, cuándo, y qué '
      r'tiene la escuadra para presentarle. El porcentaje es el del Excel \codigo{evaluacion\_tareas\_docente.xlsx}.')
    for d in lab['docente']:
        pct, falta = docente.get(d['num'], (None, None))
        e, p = estado(pct)
        w(rf'\subsection{{{tex(d["tarea"])}}}')
        w(rf'\paragraph{{Lo que dice la guía.}} {tex(d["guia"])} \textit{{Cuándo:}} {tex(d["cuando"])}.')
        w(r'\paragraph{Qué debía revisar el docente (hitos de la revisión).}')
        w(r'\begin{itemize}')
        for x in d['revisar']:
            w(rf'\item[$\square$] {tex(x)}')
        w(r'\end{itemize}')
        if d['presenta'] != ['—']:
            w(r'\paragraph{Qué tiene la escuadra para esa revisión.}')
            w(r'\begin{itemize}')
            for x in d['presenta']:
                w(rf'\item {tex(x)}')
            w(r'\end{itemize}')
        if falta and falta != '—':
            w(rf'\paragraph{{Lo que falta para que el docente lo apruebe.}} {tex(str(falta))}')
        w(rf'\paragraph{{Estado:}} {e}~({p}).')
    if lab.get('hito'):
        w(r'\subsection{Hito de la fase}')
        w(tex(lab['hito']))

    w(r'\section{Conclusión}')
    hechos = [o['nombre'] for o in lab['objetivos'] if o['pct'] >= 1]
    parcial = [o['nombre'] for o in lab['objetivos'] if 0 < o['pct'] < 1]
    nada = [o['nombre'] for o in lab['objetivos'] if o['pct'] <= 0]
    frases = []
    if hechos:
        frases.append('Cumplidos: ' + ', '.join(hechos) + '.')
    if parcial:
        frases.append('Con avance parcial: ' + ', '.join(parcial) + '.')
    if nada:
        frases.append('Sin implementar: ' + ', '.join(nada) + '.')
    w(tex(' '.join(frases)))
    pend = [o['falta'] for o in lab['objetivos'] if o['falta'] != '—']
    if pend:
        w(r'\par\smallskip Pendientes principales:')
        w(r'\begin{enumerate}')
        for x in pend:
            w(rf'\item {tex(x)}')
        w(r'\end{enumerate}')
    w(rf'\par\smallskip\noindent Repositorio: \url{{{REPO}}}')
    w(r'\end{document}')
    return '\n'.join(L) + '\n'


def compilar(carpeta, nombre):
    for _ in range(2):
        r = subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', nombre + '.tex'],
                           cwd=carpeta, capture_output=True, text=True, errors='replace')
        if r.returncode:
            print(r.stdout[-2500:])
            raise SystemExit(f'error al compilar {carpeta}/{nombre}.tex')
    for ext in ('aux', 'log', 'out', 'toc'):
        try:
            os.remove(os.path.join(carpeta, f'{nombre}.{ext}'))
        except FileNotFoundError:
            pass


def main():
    excel()
    docente = tareas_docente()
    for lab in LABS:
        carpeta = os.path.join(AQUI, lab['carpeta'])
        nombre = f'logros_lab{lab["n"]:02d}'
        with open(os.path.join(carpeta, nombre + '.tex'), 'w') as f:
            f.write(documento(lab, docente))
        compilar(carpeta, nombre)
        print(f'{lab["carpeta"]}/{nombre}.pdf')


if __name__ == '__main__':
    main()
