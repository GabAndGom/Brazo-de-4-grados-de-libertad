# Laboratorio 5: Gemelo digital, discretización y triggers PL/pgSQL (cierre de la fase 2)

Guía: [`guia_laboratorio_5.pdf`](../../guias/guia_laboratorio_5.pdf) · entrega: 27/10/2026 · estado: entregado

**Informe completo:** [`informe_lab05.pdf`](informe_lab05.pdf)

## Entregables que pide la guía 5 (Definition of Done)

| Entregable | Archivo | Estado |
|---|---|---|
| Archivos de simulación (.slx / .m) y cálculo de rangos | [`espacio_estados_brazo.m`](espacio_estados_brazo.m) | parcial: el .slx lo genera crear_gemelo_simulink.m (sin ejecutar, falta MATLAB) |
| Script SQL de lógica de servidor (funciones y triggers) | [`brazo_4gdl.sql`](../../database/scripts/brazo_4gdl.sql) | cumplido; pruebas en prueba_reglas.sql |
| Informe de cierre de la fase 2 (fidelidad del gemelo y resiliencia del backend) | [`informe_lab05.pdf`](informe_lab05.pdf) | cumplido; falta la medición con calibre y la firma |

## Programas y material de soporte

| Material | Archivo |
|---|---|
| Generador del modelo de Simulink | [`crear_gemelo_simulink.m`](crear_gemelo_simulink.m) |
| Espacio de estados en Python y su salida | [`espacio_estados_brazo.py`](espacio_estados_brazo.py) |
| Salida del cálculo | [`salida_espacio_estados.txt`](salida_espacio_estados.txt) |
| Índice de fidelidad del gemelo | [`indice_fidelidad.py`](indice_fidelidad.py) |
| Plantilla de medición con calibre | [`medicion_calibre.csv`](medicion_calibre.csv) |
| Pruebas de inyección de datos erróneos | [`prueba_reglas.sql`](../../database/scripts/prueba_reglas.sql) |
| Gemelo digital (app) | [`gemelo-digital`](../../gemelo-digital/) |

Las fuentes LaTeX del informe están en [`../../desarrollo/fuentes/laboratorios/`](../../desarrollo/fuentes/laboratorios/) y se compilan con `python3 desarrollo/compilar_documentos.py`.
