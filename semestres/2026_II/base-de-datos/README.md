# Base de datos (II-2026)

Trabajo de Bases de Datos (ETN-1000): modelo, scripts y la interfaz local del brazo.

| Carpeta / archivo | Contenido |
|---|---|
| `documentacion/base_datos_brazo.pdf` | Documento completo: objetivos de las guías, requerimientos, E-R, modelo lógico, normalización paso a paso, tags ISA, reglas, DFD, mockups → consultas, diccionario de datos e instalación |
| `scripts/brazo_4gdl.sql` | DDL (15 tablas), índices, trigger de rango, vistas y datos de la planta |
| `scripts/prueba_reglas.sql` | Prueba de NOT NULL, CHECK, FK, UNIQUE y del trigger (no deja datos) |
| `scripts/consultas_kpi.sql` | 14 consultas del dashboard, una por elemento de los mockups |
| `modelo/` | Modelo E-R preliminar del equipo |
| `mockups/` | Mockups de la interfaz y organigrama (Lab 2) |
| `interfaz/` | Capturas de la interfaz local |

Los scripts tienen la sintaxis validada con el analizador de PostgreSQL (`pglast`), pero todavía no se ejecutaron en un servidor:

```bash
createdb brazo4gdl
psql -d brazo4gdl -f scripts/brazo_4gdl.sql
psql -d brazo4gdl -f scripts/prueba_reglas.sql
```

Para regenerar el documento: `cd documentacion && python3 generar_diccionario.py && pdflatex base_datos_brazo.tex` (dos veces).
