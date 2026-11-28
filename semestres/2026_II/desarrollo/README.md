# Desarrollo (material de trabajo, no entregable)

Lo que el equipo usa para producir los entregables. No aparece en la página publicada.

| Carpeta | Contenido |
|---|---|
| `fuentes/` | Fuentes LaTeX de todos los informes y manuales, con sus imágenes y figuras, y los generadores (planos DXF, diccionario de datos, esquemas de medidas). Misma estructura que `semestres/2026_II/`. |
| `fuentes/modelo-3d/levantamiento/` | Levantamiento de medidas: fotos, planilla, esquemas y medidas tomadas del modelo de Inventor |
| `seguimiento/` | Seguimiento interno: evaluación de las tareas del docente, objetivos por laboratorio (Excel) y documentos de logros |
| `notas/` | Notas técnicas de trabajo |

## Regenerar los entregables

```bash
python3 desarrollo/compilar_documentos.py                                  # todos los informes y manuales en PDF
python3 desarrollo/fuentes/documentacion/planos_isa/generar_planos_v2.py   # planos v2.0 (DXF y PDF)
python3 desarrollo/fuentes/database/documentacion/generar_diccionario.py   # diccionario de datos (antes de compilar)
python3 desarrollo/seguimiento/generar_logros.py                           # Excel de objetivos y documentos de logros
```

Cada PDF entregable se deja en su carpeta pública (`laboratorios/`, `gemelo-digital/manual/`,
`database/documentacion/`, `modelo-3d/informe/`).
