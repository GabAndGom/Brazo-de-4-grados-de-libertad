# Laboratorio 4: Identificación, espacio de estados y estructura física de la base

Guía: [`guia_laboratorio_4.pdf`](../../guias/guia_laboratorio_4.pdf) · entrega: 29/09/2026 · estado: entregado

**Informe completo:** [`informe_lab04.pdf`](informe_lab04.pdf)

## Entregables que pide la guía 4 (Definition of Done)

| Entregable | Archivo | Estado |
|---|---|---|
| Informe (bitácora de la fase 2, parte 1) | [`informe_lab04.pdf`](informe_lab04.pdf) | cumplido |
| Script SQL ejecutable (.sql) | [`brazo_4gdl.sql`](../../database/scripts/brazo_4gdl.sql) | cumplido; registro en registro_ejecucion.txt |
| Archivo de telemetría cruda del escalón (.csv) | [`datos`](datos/) | parcial: ensayos con el PLC simulado; falta la corrida en la planta |
| Modelo continuo identificado y matrices de espacio de estados | [`informe_lab04.pdf`](informe_lab04.pdf) | parcial: K y t_d; tau no medible sin sensor |

## Programas y material de soporte

| Material | Archivo |
|---|---|
| Prueba escalón automatizada y análisis | [`prueba_escalon.py`](prueba_escalon.py) |
| Registro de ejecución del script SQL | [`registro_ejecucion.txt`](../../database/scripts/registro_ejecucion.txt) |
| Cálculo de las matrices (Python) | [`espacio_estados_brazo.py`](../lab05_gemelo_y_triggers/espacio_estados_brazo.py) |

Las fuentes LaTeX del informe están en [`../../desarrollo/fuentes/laboratorios/`](../../desarrollo/fuentes/laboratorios/) y se compilan con `python3 desarrollo/compilar_documentos.py`.
