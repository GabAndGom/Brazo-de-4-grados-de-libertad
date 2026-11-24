# Gestión II/2026 · Brazo XK-JS1-1 (4 GDL)

ETN-902 Sistemas de Control II · ETN-1034 Aplicación de Técnicas de Control · ETN-1000 Bases de Datos.

Esta carpeta contiene **solo entregables**: informes, planos, programas y scripts que piden las guías. Lo que
el equipo usa para producirlos (fuentes LaTeX, generadores, seguimiento interno) está aparte en
[`desarrollo/`](desarrollo/) y no se publica en la página.

| Carpeta | Contenido |
|---|---|
| [`guias/`](guias/) | Guías de laboratorio 1 a 8 (docente) |
| [`laboratorios/`](laboratorios/) | **Un informe completo por laboratorio** y el índice de sus entregables |
| [`documentacion/planos_isa/`](documentacion/planos_isa/) | P&ID (ISA-5.1) y esquema eléctrico (IEC 60617): versión 2.0 en DWG, DXF y PDF, e históricos |
| [`documentacion/manuales_inversa/`](documentacion/manuales_inversa/) | Ingeniería inversa del laboratorio 1: informe con ficha técnica y diagrama de bloques |
| [`database/`](database/) | Scripts SQL (DDL, triggers, pruebas, consultas, respaldos), modelo E-R, mockups y documento de la base |
| [`gemelo-digital/`](gemelo-digital/) | Programas: app del gemelo (middleware, API, dashboard, Modbus) y programas del PLC; manuales en PDF |
| [`programas-plc/`](programas-plc/) | Programa original del PLC (activo histórico, ingeniería inversa) |
| [`modelo-3d/`](modelo-3d/) | Cinemática del brazo (código y parámetros) e informe del modelo 3D |

## Entregables por laboratorio

| Lab | Informe | Entregables principales |
|---|---|---|
| 1 | [informe_lab01.pdf](laboratorios/lab01_auditoria/informe_lab01.pdf) | ficha técnica, discrepancias Kaizen, diagrama de bloques, arquitectura de 3 capas |
| 2 | [informe_lab02.pdf](laboratorios/lab02_planos_e_interfaces/informe_lab02.pdf) | [P&ID v2.0](documentacion/planos_isa/pid/), [eléctrico v2.0](documentacion/planos_isa/electrico/), [mockups](database/mockups/) |
| 3 | [informe_lab03.pdf](laboratorios/lab03_git_y_modelo_er/informe_lab03.pdf) y [cierre de la fase 1](laboratorios/lab03_git_y_modelo_er/informe_cierre_fase1.pdf) | [modelo E-R en 3FN](database/documentacion/base_datos_brazo.pdf), [git log](laboratorios/lab03_git_y_modelo_er/git_log.txt) |
| 4 | [informe_lab04.pdf](laboratorios/lab04_identificacion_y_ddl/informe_lab04.pdf) | [script SQL](database/scripts/brazo_4gdl.sql), [CSV del escalón](laboratorios/lab04_identificacion_y_ddl/datos/) |
| 5 | [informe_lab05.pdf](laboratorios/lab05_gemelo_y_triggers/informe_lab05.pdf) | [.m / Simulink](laboratorios/lab05_gemelo_y_triggers/), [triggers PL/pgSQL](database/scripts/) |
| 6 | [informe_lab06.pdf](laboratorios/lab06_control_discreto_y_middleware/informe_lab06.pdf) | [programa del PLC](gemelo-digital/plc/), [middleware](gemelo-digital/app/) |
| 7 | [informe_lab07.pdf](laboratorios/lab07_lqr_dashboard_y_rbac/informe_lab07.pdf) | [dashboard](gemelo-digital/app/ui/dashboard.html), [certificado RBAC](laboratorios/lab07_lqr_dashboard_y_rbac/) |
| 8 | [informe_lab08.pdf](laboratorios/lab08_modbus_api_y_cierre/informe_lab08.pdf) | [manual técnico](gemelo-digital/manual/manual_tecnico.pdf), [API REST y Modbus](gemelo-digital/app/) |
