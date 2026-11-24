# Laboratorio 7: LQR, dashboard y control de acceso por roles

Guía: [`guia_laboratorio_7.pdf`](../../guias/guia_laboratorio_7.pdf) · entrega: 08/12/2026 · estado: avance

**Informe completo:** [`informe_lab07.pdf`](informe_lab07.pdf)

## Entregables que pide la guía 7 (Definition of Done)

| Entregable | Archivo | Estado |
|---|---|---|
| Código LQR en el PLC | [`lqr_brazo.py`](lqr_brazo.py) | pendiente: no viable con el hardware actual; K calculada en simulación |
| Frontend del dashboard ERP conectado a PostgreSQL | [`dashboard.html`](../../gemelo-digital/app/ui/dashboard.html) | cumplido (probado con el PLC simulado) |
| Certificado de seguridad RBAC | [`certificado_rbac_20261118_2234.md`](certificado_rbac_20261118_2234.md) | cumplido: 18 de 18 pruebas; falta la firma del auxiliar |
| Informe del laboratorio | [`informe_lab07.pdf`](informe_lab07.pdf) | avance |

## Programas y material de soporte

| Material | Archivo |
|---|---|
| LQR en MATLAB y salida | [`lqr_brazo.m`](lqr_brazo.m) |
| Salida del cálculo LQR | [`salida_lqr.txt`](salida_lqr.txt) |
| Pruebas RBAC (genera el certificado) | [`prueba_rbac.py`](prueba_rbac.py) |
| Consultas KPI | [`consultas_kpi.sql`](../../database/scripts/consultas_kpi.sql) |
| API que alimenta el dashboard | [`api_erp.py`](../../gemelo-digital/app/api_erp.py) |

Las fuentes LaTeX del informe están en [`../../desarrollo/fuentes/laboratorios/`](../../desarrollo/fuentes/laboratorios/) y se compilan con `python3 desarrollo/compilar_documentos.py`.
