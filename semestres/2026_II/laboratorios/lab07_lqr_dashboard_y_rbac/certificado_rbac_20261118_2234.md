# Certificado de seguridad RBAC · brazo XK-JS1-1

- Fecha: 2026-11-18 22:34
- Servidor: `https://127.0.0.1:8444`
- Usuarios de prueba: operador `prueba_op`, observador `prueba_obs`
- Resultado: **18 de 18 pruebas aprobadas**

| Prueba | Petición | Esperado | Obtenido | Resultado | Respuesta del servidor |
|---|---|---|---|---|---|
| API sin token | GET /api/v1/kpi | 401 | 401 | APROBADA | falta un token válido: POST /api/v1/token |
| Token inventado (32 bytes aleatorios) | GET /api/v1/alertas/activas | 401 | 401 | APROBADA | falta un token válido: POST /api/v1/token |
| Token vacío en la cabecera | GET /api/v1/kpi | 401 | 401 | APROBADA | falta un token válido: POST /api/v1/token |
| Token del observador alterado en 1 carácter | GET /api/v1/kpi | 401 | 401 | APROBADA | falta un token válido: POST /api/v1/token |
| Estado en vivo sin token | GET /api/estado | 401 | 401 | APROBADA | sesión vencida: vuelva a ingresar |
| Orden de movimiento sin token | POST /api/orden/mover | 401 | 401 | APROBADA | sesión vencida: vuelva a ingresar |
| Orden de movimiento con token inventado | POST /api/orden/mover | 401 | 401 | APROBADA | sesión vencida: vuelva a ingresar |
| Observador: orden de movimiento | POST /api/orden/mover | 403 | 403 | APROBADA | su usuario es observador: solo puede ver el brazo |
| Observador: orden de garra | POST /api/orden/garra | 403 | 403 | APROBADA | su usuario es observador: solo puede ver el brazo |
| Observador: tomar el mando | POST /api/mando | 403 | 403 | APROBADA | su usuario es observador: solo puede ver el brazo |
| Observador: rearmar la planta en la base | POST /api/v1/planta/rearmar | 403 | 403 | APROBADA | solo un operador puede rearmar la planta |
| Observador: historial de sesiones | GET /api/v1/sesiones | 403 | 403 | APROBADA | solo un operador puede ver el historial de sesiones |
| Observador: lectura de telemetría (permitida) | GET /api/v1/telemetria/planta/1 | 200 | 200 | APROBADA | correcto |
| Observador: KPI (permitido) | GET /api/v1/kpi | 200 | 200 | APROBADA | correcto |
| Operador: historial de sesiones (permitido) | GET /api/v1/sesiones | 200 | 200 | APROBADA | correcto |
| Menú de administración desde la red | GET /api/app | 403 | 403 | APROBADA | solo desde la PC del laboratorio |
| Cambio de modo desde la red | POST /api/app/modo | 403 | 403 | APROBADA | solo desde la PC del laboratorio |
| Clave incorrecta al pedir token | POST /api/v1/token | 401 | 401 | APROBADA | usuario o contraseña incorrectos |

401 = sin sesión válida; 403 = sesión válida sin permiso para esa acción.

Ejecutó: ____________________ (auxiliar)    Revisó: ____________________ (docente)
