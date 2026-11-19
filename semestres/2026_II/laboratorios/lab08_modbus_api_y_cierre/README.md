# Laboratorio 8: Modbus, API REST y cierre del proyecto (avance)

Guía: [`guia_laboratorio_8.pdf`](../../guias/guia_laboratorio_8.pdf) · entrega: 22/12/2026

**Informe:** [`informe_lab08.pdf`](informe_lab08.pdf) (fuente: `informe_lab08.tex`, se compila con `pdflatex` dos veces desde esta carpeta).

| Entregable / material | Ubicación |
|---|---|
| Manual técnico | [`../../gemelo-digital/manual/tecnico/manual_tecnico.pdf`](../../gemelo-digital/manual/tecnico/manual_tecnico.pdf) |
| Pasarela Modbus TCP y cliente TCP/RTU con estadísticas de CRC | [`../../gemelo-digital/app/modbus.py`](../../gemelo-digital/app/modbus.py), [`salida_modbus_tcp.txt`](salida_modbus_tcp.txt) |
| Esclavo Modbus RTU en el PLC (no probado) | [`../../gemelo-digital/plc/modbus_esclavo_rtu.awl`](../../gemelo-digital/plc/modbus_esclavo_rtu.awl) |
| API REST de históricos | [`../../gemelo-digital/app/api_erp.py`](../../gemelo-digital/app/api_erp.py) |
| Auditoría de endpoints concurrentes | [`prueba_api_concurrente.py`](prueba_api_concurrente.py), [`salida_api_concurrente.txt`](salida_api_concurrente.txt) |
| Respaldos programados | [`../../database/scripts/respaldo.sh`](../../database/scripts/respaldo.sh), [`respaldo.bat`](../../database/scripts/respaldo.bat) |
