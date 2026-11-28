#!/usr/bin/env python3
"""Compila las fuentes LaTeX de desarrollo/fuentes/ y deja cada PDF entregable en su carpeta pública.

    python3 compilar_documentos.py            todos
    python3 compilar_documentos.py lab04      solo los que contienen ese texto en la ruta

Las fuentes viven aquí (desarrollo/fuentes/, misma estructura que semestres/2026_II/) y los PDF que pide cada
guía se publican en laboratorios/, gemelo-digital/manual/, database/documentacion/ y modelo-3d/informe/.
Cada documento se compila tres veces (índice y referencias) y se borran los auxiliares.
"""
import os
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
FUENTES = os.path.join(AQUI, 'fuentes')
SEMESTRE = os.path.dirname(AQUI)

LABS = ['lab01_auditoria', 'lab02_planos_e_interfaces', 'lab03_git_y_modelo_er', 'lab04_identificacion_y_ddl', 'lab05_gemelo_y_triggers',
        'lab06_control_discreto_y_middleware', 'lab07_lqr_dashboard_y_rbac', 'lab08_modbus_api_y_cierre']
# fuente (relativa a fuentes/) -> PDF público (relativo a semestres/2026_II/); None = queda junto a la fuente
DOCUMENTOS = {f'laboratorios/{l}/informe_{l[:5]}.tex': f'laboratorios/{l}/informe_{l[:5]}.pdf' for l in LABS}
DOCUMENTOS.update({
    'laboratorios/lab03_git_y_modelo_er/informe_cierre_fase1.tex': 'laboratorios/lab03_git_y_modelo_er/informe_cierre_fase1.pdf',
    'gemelo-digital/manual/tecnico/manual_tecnico.tex': 'gemelo-digital/manual/manual_tecnico.pdf',
    'gemelo-digital/manual/guia_completa_brazo.tex': 'gemelo-digital/manual/guia_completa_brazo.pdf',
    'gemelo-digital/manual/arquitectura_gemelo_digital.tex': 'gemelo-digital/manual/arquitectura_gemelo_digital.pdf',
    'gemelo-digital/manual/manual_gemelo_digital.tex': 'gemelo-digital/manual/manual_gemelo_digital.pdf',
    'gemelo-digital/manual/manual_linux.tex': 'gemelo-digital/manual/manual_linux.pdf',
    'gemelo-digital/manual/manual_windows.tex': 'gemelo-digital/manual/manual_windows.pdf',
    'database/documentacion/base_datos_brazo.tex': 'database/documentacion/base_datos_brazo.pdf',
    'modelo-3d/informe/informe_cinematica_modelo_3d.tex': 'modelo-3d/informe/informe_cinematica_modelo_3d.pdf',
    'documentacion/planos_isa/guia/guia_lectura_planos.tex': 'documentacion/planos_isa/guia_lectura_planos.pdf',
    'modelo-3d/levantamiento/planilla_mediciones.tex': None,
})
# copias que pide la guía 3 en otra carpeta (destino -> copia)
COPIAS = {'laboratorios/lab01_auditoria/informe_lab01.pdf': 'documentacion/manuales_inversa/informe_1_auditoria_y_requerimientos.pdf'}


def compilar(fuente, destino):
    carpeta, archivo = os.path.split(os.path.join(FUENTES, fuente))
    nombre = archivo[:-4]
    for _ in range(3):
        r = subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', archivo], cwd=carpeta,
                           capture_output=True, text=True, errors='replace')
        if r.returncode:
            print(r.stdout[-2000:])
            raise SystemExit(f'error al compilar {fuente}')
    for ext in ('aux', 'log', 'out', 'toc', 'lof', 'lot'):
        try:
            os.remove(os.path.join(carpeta, f'{nombre}.{ext}'))
        except FileNotFoundError:
            pass
    if destino:
        final = os.path.join(SEMESTRE, destino)
        os.makedirs(os.path.dirname(final), exist_ok=True)
        shutil.move(os.path.join(carpeta, nombre + '.pdf'), final)
        if destino in COPIAS:
            shutil.copyfile(final, os.path.join(SEMESTRE, COPIAS[destino]))
    print(f'{fuente}  ->  {destino or "(junto a la fuente)"}')


def main():
    filtro = sys.argv[1] if len(sys.argv) > 1 else ''
    for fuente, destino in DOCUMENTOS.items():
        if filtro in fuente:
            compilar(fuente, destino)


if __name__ == '__main__':
    main()
