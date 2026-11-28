# App del gemelo digital del brazo XK-JS1-1

Una sola app, para **Linux y Windows**, con un menú de inicio de tres modos:

| Modo | Para qué |
|---|---|
| **Simulación** | practicar sin brazo ni cable (PLC simulado dentro de la app) |
| **Operación local** | ver y mandar el brazo real desde esta PC (cable USB-PPI al puerto 0 del PLC) |
| **Operación por red local** | lo mismo, y además celulares y otras PC de la red entran con usuario y contraseña (`https://IP:8443/`), o sin contraseña como **observadores libres** (solo ver) |

Desde el menú también se crean los usuarios del acceso por red. El botón **Menú** de la barra del gemelo
vuelve al menú para cambiar de modo sin cerrar la app.

## Abrir

- **Linux**: menú de aplicaciones → *Gemelo digital del brazo* (se crea una vez con `./instalar_acceso.sh`),
  o `./iniciar_gemelo.sh` en una terminal. Si la VM de Windows XP está abierta, el USB del cable debe estar
  **desmarcado** en su menú Dispositivos → USB.
- **Windows**: instale Python 3 (python.org, marcando *Add python.exe to PATH*) y haga doble clic en
  `Gemelo digital.bat`. `Crear acceso directo.bat` lo pone en el escritorio.

Para comprobar el cable sin mover nada: `python3 probar_plc.py` (Windows: `Probar conexion PLC.bat`).

## Observadores libres

En la tarjeta *Operación por red local* del menú, la casilla **Observadores libres** deja entrar sin usuario ni
contraseña, solo para ver: el QR pasa a apuntar a `https://IP:8443/libre` y cada persona entra como `visita-N`.
El servidor rechaza las órdenes y el mando de una visita; al desmarcar la casilla sus sesiones se cierran. Viene
apagada al abrir la app (también se activa con `--observadores-libres`). Mandar el brazo sigue pidiendo un operador.

## Telemetría, dashboard, API y Modbus (laboratorios 6 a 8)

- **Telemetría**: la app guarda siempre un CSV por sesión en `telemetria/`. Si la PC tiene PostgreSQL con la
  base creada (`createdb brazo4gdl` y `psql -d brazo4gdl -f database/scripts/brazo_4gdl.sql`) y el paquete
  `psycopg` (`pip install "psycopg[binary]"`), además inserta una muestra por segundo y por variable, los cambios
  de señales, las alarmas, las órdenes y los ingresos. Otra base: variable `BRAZO_PG` o `base_datos.json` con
  `{"conninfo": "dbname=... user=... host=..."}`. Sin base, la app funciona igual. `--sin-telemetria` lo apaga.
- **Dashboard**: botón «Dashboard» de la barra (`/dashboard.html`): indicadores (con la eficiencia
  homeostática), series de tiempo, alarmas, órdenes e ingresos. El observador solo lee.
- **API REST** (guía 8): `POST /api/v1/token` con `{"usuario": ..., "clave": ...}` devuelve un token;
  después `GET /api/v1/telemetria/planta/1?tag=ZI-102&desde=...&formato=csv`, `/api/v1/alertas/activas`,
  `/api/v1/kpi`, `/api/v1/ciclos`, `/api/v1/ordenes`, `/api/v1/sesiones` (operador) con
  `Authorization: Bearer <token>`.
- **Modbus TCP**: `--modbus` (puerto 5020) publica el estado como registros 40001-40015 (mapa en `modbus.py`),
  solo lectura. Prueba: `python3 modbus.py cliente --tcp IP:5020 --repetir 100`.

## Documentos (carpeta `documentos`)

- `manual_linux.pdf` y `manual_windows.pdf`: instalación y uso en cada sistema.
- `guia_completa_brazo.pdf`: la planta, los programas del PLC en ladder, el modelado y el software.
- `arquitectura_gemelo_digital.pdf`: páginas web, protocolo PPI y modos de mando en detalle.

## Contenido

| Archivo | Para qué |
|---|---|
| `gemelo_brazo.py` | Programa principal: menú de modos, servidor local y de red, API |
| `brazo.py`, `ppi.py`, `serie.py` | Comunicación con el PLC (PPI sobre el puerto serie de Linux o Windows), perfiles, estimador y PLC simulado |
| `acceso.py`, `usuarios.py`, `certificado_tls.py` | Usuarios, sesiones y certificado HTTPS del acceso por red |
| `ventana.py` | Ventana propia: GTK + WebKit en Linux, Edge en modo aplicación en Windows |
| `menu.html`, `ui/` | Interfaz: menú y página del gemelo |
| `probar_plc.py` | Diagnóstico de solo lectura |
| `telemetria.py` | Registrador: telemetría a CSV (`telemetria/`) y a PostgreSQL (muestras, señales, alarmas, órdenes, sesiones) |
| `api_erp.py`, `ui/dashboard.html` | API REST de históricos (`/api/v1/...`, token Bearer) y dashboard con KPI y series de tiempo |
| `modbus.py` | Pasarela Modbus TCP (opción `--modbus`), cliente de prueba TCP/RTU con estadísticas de CRC |
| `*.sh` / `*.bat` | Lanzadores de Linux / Windows |
| `empaquetar.py` | (Repositorio) actualiza `ui/` y exporta la app autónoma |

Datos propios de cada PC (no se comparten ni se suben al repositorio): `usuarios.json`,
`tls_certificado.pem`, `tls_clave.pem`, `calibracion.json`, `registro_gemelo.log`, `base_datos.json` y la
carpeta `telemetria/`.
