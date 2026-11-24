# Laboratorio 6: Control discreto en el PLC y middleware de telemetría

Guía: [`guia_laboratorio_6.pdf`](../../guias/guia_laboratorio_6.pdf) · entrega: 24/11/2026 · estado: en curso

**Informe completo:** [`informe_lab06.pdf`](informe_lab06.pdf)

## Entregables que pide la guía 6 (Definition of Done)

| Entregable | Archivo | Estado |
|---|---|---|
| Código fuente del PLC (.mwp) con interrupción y ecuación de diferencias | [`plc`](../../gemelo-digital/plc/) | parcial: brazo_gemelo.mwp + pi_lazo_flotante.awl (sin cargar en el PLC) |
| Flujo del middleware (Python) con JSON e inserción en PostgreSQL | [`telemetria.py`](../../gemelo-digital/app/telemetria.py) | cumplido (probado con el PLC simulado) |
| Bitácora lazo abierto frente a lazo cerrado | [`informe_lab06.pdf`](informe_lab06.pdf) | pendiente: no hay sensor de posición |
| Informe del laboratorio | [`informe_lab06.pdf`](informe_lab06.pdf) | cumplido |

## Programas y material de soporte

| Material | Archivo |
|---|---|
| Diseño del PI y prueba de lazo flotante | [`pi_discreto.py`](pi_discreto.py) |
| Lo mismo en MATLAB | [`pi_discreto.m`](pi_discreto.m) |
| Registro de la prueba de lazo flotante (emulador) | [`lazo_flotante_EMULADO.csv`](lazo_flotante_EMULADO.csv) |
| Middleware completo | [`app`](../../gemelo-digital/app/) |

Las fuentes LaTeX del informe están en [`../../desarrollo/fuentes/laboratorios/`](../../desarrollo/fuentes/laboratorios/) y se compilan con `python3 desarrollo/compilar_documentos.py`.
