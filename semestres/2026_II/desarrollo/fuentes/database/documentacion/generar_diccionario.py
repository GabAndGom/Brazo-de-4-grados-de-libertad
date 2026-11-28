#!/usr/bin/env python3
"""Genera diccionario.tex (diccionario de datos) leyendo ../scripts/brazo_4gdl.sql.

    python3 generar_diccionario.py

Así el diccionario del documento nunca se separa del script: si cambia una columna, se vuelve a generar.
"""
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
SQL = os.path.join(AQUI, '..', '..', '..', '..', 'database', 'scripts', 'brazo_4gdl.sql')   # entregable público

# descripción de las columnas que no tienen comentario en el script
DESC = {
    'id': 'identificador (clave sustituta)',
    'sistema.nombre': 'nombre de la planta', 'sistema.tipo': 'tipo de planta', 'sistema.plc': 'PLC que la controla',
    'eje.codigo': 'Z (base), X, Y, G (garra)', 'eje.nombre': 'nombre del grado de libertad',
    'eje.tipo_mov': 'rotacional, lineal o binario', 'eje.unidad': 'unidad de la posición',
    'eje.pulsos_unidad': 'pulsos por unidad (NULL en la garra)', 'eje.lazo_isa': 'número de lazo ISA (101 a 104)',
    'punto_io.direccion': 'dirección en el PLC (I0.1, Q0.5...)', 'punto_io.tag_isa': 'tag ISA-5.1 de la señal',
    'punto_io.tipo_senal': 'DI, DO o PTO', 'punto_io.descripcion': 'qué hace la señal',
    'punto_io.eje_id': 'eje al que pertenece (NULL: señal general del panel)',
    'variable.tag_isa': 'tag ISA-5.1 de la variable', 'variable.clase': 'PV, MV o DV',
    'variable.nombre': 'nombre de la magnitud', 'variable.unidad': 'unidad de ingeniería',
    'variable.rango_min': 'mínimo admisible (lo usa el trigger)', 'variable.rango_max': 'máximo admisible (lo usa el trigger)',
    'programa_plc.nombre': 'nombre del programa ladder', 'programa_plc.perfil_app': 'perfil con que la app lo reconoce',
    'programa_plc.firma': 'valores de memoria que lo identifican', 'programa_plc.descripcion': 'qué hace',
    'alarma.codigo': 'código corto de la alarma', 'alarma.severidad': '1 aviso, 2 falla, 3 crítica', 'alarma.descripcion': 'significado',
    'rol.nombre': 'observador u operador',
    'usuario.nombre': 'nombre de ingreso', 'usuario.rol_id': 'rol del usuario', 'usuario.clave_hash': 'contraseña en PBKDF2 (nunca en claro)',
    'usuario.creado_en': 'fecha de alta',
    'sesion.usuario_id': 'usuario (NULL si el nombre no existe)', 'sesion.nombre_usado': 'nombre que se escribió',
    'sesion.ip': 'dirección IP del equipo', 'sesion.instante': 'momento del intento', 'sesion.exito': 'ingreso aceptado o no',
    'sesion.fin': 'cierre de la sesión',
    'ciclo_operacion.sistema_id': 'planta', 'ciclo_operacion.programa_id': 'programa reconocido en el PLC',
    'ciclo_operacion.modo': 'simulacion, local o red', 'ciclo_operacion.inicio': 'inicio del ciclo', 'ciclo_operacion.fin': 'fin (NULL: en curso)',
    'muestra.ciclo_id': 'ciclo en que se tomó', 'muestra.variable_id': 'variable medida', 'muestra.instante': 'marca de tiempo',
    'muestra.valor': 'valor en la unidad de la variable',
    'estado_io.ciclo_id': 'ciclo', 'estado_io.punto_id': 'señal que cambió', 'estado_io.instante': 'marca de tiempo',
    'estado_io.valor': 'nuevo estado (0/1)',
    'orden.ciclo_id': 'ciclo', 'orden.usuario_id': 'quién la dio (NULL: PC local)', 'orden.instante': 'marca de tiempo',
    'orden.tipo': 'homing, mover, garra, detener...', 'orden.aceptada': 'si la app la ejecutó', 'orden.motivo': 'motivo del rechazo',
    'orden_parametro.orden_id': 'orden', 'orden_parametro.eje_id': 'eje de destino', 'orden_parametro.valor': 'destino en la unidad del eje',
    'evento_alarma.alarma_id': 'alarma del catálogo', 'evento_alarma.ciclo_id': 'ciclo', 'evento_alarma.instante': 'marca de tiempo',
    'evento_alarma.activa': 'se activa (1) o se normaliza (0)', 'evento_alarma.detalle': 'texto adicional',
}


def tex(s):
    return (s.replace('\\', r'\textbackslash{}').replace('_', r'\_').replace('%', r'\%').replace('&', r'\&')
            .replace('#', r'\#').replace('$', r'\$').replace('{', r'\{').replace('}', r'\}'))


def leer():
    sql = open(SQL, encoding='utf-8').read()
    tablas = []
    for m in re.finditer(r'CREATE TABLE (\w+) \((.*?)\n\);', sql, re.S):
        nombre, cuerpo = m.group(1), m.group(2)
        cols, extra = [], []
        for linea in cuerpo.split('\n'):
            linea = linea.strip()
            if not linea:
                continue
            comentario = ''
            if '--' in linea:
                linea, comentario = [p.strip() for p in linea.split('--', 1)]
            linea = linea.rstrip(',')
            if re.match(r'(UNIQUE|CHECK|PRIMARY KEY) ?\(', linea):
                extra.append(linea)
                continue
            p = re.match(r'(\w+)\s+([A-Z]+(?:\(\d+(?:,\d+)?\))?(?: PRECISION)?)\s*(.*)', linea)
            if not p:
                continue
            col, tipo, resto = p.groups()
            restr = []
            if 'PRIMARY KEY' in resto: restr.append('PK')
            r = re.search(r'REFERENCES (\w+)', resto)
            if r: restr.append('FK→' + r.group(1))
            if 'UNIQUE' in resto: restr.append('UQ')
            c = re.search(r'CHECK \((.*)\)', resto)
            if c: restr.append('CHECK')
            d = re.search(r'DEFAULT (\S+)', resto)
            if d: restr.append('DEFAULT ' + d.group(1))
            nulo = 'no' if ('NOT NULL' in resto or 'PRIMARY KEY' in resto or 'SERIAL' in tipo) else 'sí'
            desc = comentario or DESC.get(f'{nombre}.{col}') or DESC.get(col, '')
            cols.append((col, tipo, nulo, ', '.join(restr), desc))
        tablas.append((nombre, cols, extra))
    return tablas


def main():
    out = [r'% Generado por generar_diccionario.py a partir de ../scripts/brazo_4gdl.sql: no editar a mano']
    for nombre, cols, extra in leer():
        out.append(r'\subsection*{\codigo{' + tex(nombre) + '}}')
        out.append(r'\begin{longtable}{>{\ttfamily\raggedright}p{2.6cm} >{\ttfamily\raggedright}p{2.5cm} c >{\raggedright\footnotesize}p{3.6cm} >{\raggedright\arraybackslash}p{4.5cm}}')
        out.append(r'\toprule \textrm{\textbf{Columna}} & \textrm{\textbf{Tipo}} & \textbf{Nulo} & \textbf{Restricción} & \textbf{Descripción}\\ \midrule')
        for col, tipo, nulo, restr, desc in cols:
            out.append(f'{tex(col)} & {tex(tipo)} & {nulo} & {tex(restr).replace("→", "$\\to$")} & {tex(desc)}\\\\')
        if extra:
            out.append(r'\midrule \multicolumn{5}{l}{\small Restricciones de tabla: \texttt{' + tex('; '.join(extra)) + r'}}\\')
        out.append(r'\bottomrule \end{longtable}')
    with open(os.path.join(AQUI, 'diccionario.tex'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    print('diccionario.tex:', len(leer()), 'tablas')


if __name__ == '__main__':
    main()
