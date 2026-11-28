# Laboratorio 8: Modbus, API REST y cierre del proyecto

Guía: [`guia_laboratorio_8.pdf`](../../guias/guia_laboratorio_8.pdf) · entrega: 22/12/2026 · estado: avance

**Informe completo:** [`informe_lab08.pdf`](informe_lab08.pdf)

## Entregables que pide la guía 8 (Definition of Done)

| Entregable | Archivo | Estado |
|---|---|---|
| Repositorio GitHub unificado final | [`Brazo-de-4-grados-de-libertad`](https://github.com/GabAndGom/Brazo-de-4-grados-de-libertad) | parcial |
| Manual técnico del ciclo de vida y Kaizen (PDF) con ORCID | [`manual_tecnico.pdf`](../../gemelo-digital/manual/manual_tecnico.pdf) | parcial: faltan ORCID y firmas |
| Demostración física en lazo cerrado con Modbus | [`informe_lab08.pdf`](informe_lab08.pdf) | pendiente: sensor de posición y red física |
| Informe del laboratorio | [`informe_lab08.pdf`](informe_lab08.pdf) | avance |

## Programas y material de soporte

| Material | Archivo |
|---|---|
| Pasarela Modbus TCP y cliente con estadísticas de CRC | [`modbus.py`](../../gemelo-digital/app/modbus.py) |
| Resultado de la prueba Modbus | [`salida_modbus_tcp.txt`](salida_modbus_tcp.txt) |
| Esclavo Modbus RTU en el PLC (no probado) | [`modbus_esclavo_rtu.awl`](../../gemelo-digital/plc/modbus_esclavo_rtu.awl) |
| API REST de históricos | [`api_erp.py`](../../gemelo-digital/app/api_erp.py) |
| Auditoría de endpoints concurrentes | [`prueba_api_concurrente.py`](prueba_api_concurrente.py) |
| Resultado de la auditoría | [`salida_api_concurrente.txt`](salida_api_concurrente.txt) |
| Respaldos programados (Linux / Windows) | [`respaldo.sh`](../../database/scripts/respaldo.sh) |
| Manuales de uso de la app | [`manual`](../../gemelo-digital/manual/) |

Las fuentes LaTeX del informe están en [`../../desarrollo/fuentes/laboratorios/`](../../desarrollo/fuentes/laboratorios/) y se compilan con `python3 desarrollo/compilar_documentos.py`.
