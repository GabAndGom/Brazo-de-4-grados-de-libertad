# Base de datos (II-2026)

Trabajo de Bases de Datos (ETN-1000): modelo, scripts y la interfaz local del brazo.

| Carpeta / archivo | Contenido |
|---|---|
| `documentacion/base_datos_brazo.pdf` | Documento completo: objetivos de las guías, requerimientos, E-R, modelo lógico, normalización paso a paso, tags ISA, reglas, DFD, mockups → consultas, diccionario de datos e instalación |
| `scripts/brazo_4gdl.sql` | DDL (15 tablas), índices, trigger de rango, vistas y datos de la planta |
| `scripts/prueba_reglas.sql` | Prueba de NOT NULL, CHECK, FK, UNIQUE y del trigger (no deja datos) |
| `scripts/consultas_kpi.sql` | 14 consultas del dashboard, una por elemento de los mockups |
| `scripts/datos_sinteticos.sql` | Datos de prueba (18 000 muestras, órdenes, sesiones y alarmas sintéticas; no son mediciones) |
| `scripts/registro_ejecucion.txt` | Salida de la ejecución en PostgreSQL 16.2: creación, pruebas, datos sintéticos, consultas e índice |
| `modelo/` | Modelo E-R preliminar del equipo |
| `mockups/` | Mockups de la interfaz y organigrama (Lab 2) |
| `interfaz/` | Capturas de la interfaz local |

Los scripts se ejecutaron en PostgreSQL 16.2 el 12/11/2026 (PC de desarrollo): la salida completa está en [`scripts/registro_ejecucion.txt`](scripts/registro_ejecucion.txt). Para repetirlo en la PC del laboratorio:

```bash
createdb brazo4gdl
psql -d brazo4gdl -f scripts/brazo_4gdl.sql
psql -d brazo4gdl -f scripts/prueba_reglas.sql
psql -d brazo4gdl -f scripts/datos_sinteticos.sql
psql -d brazo4gdl -f scripts/consultas_kpi.sql
```

El documento [`documentacion/base_datos_brazo.pdf`](documentacion/base_datos_brazo.pdf) se regenera con `python3 desarrollo/fuentes/database/documentacion/generar_diccionario.py` y `python3 desarrollo/compilar_documentos.py base_datos` (fuentes en `desarrollo/fuentes/database/`).
