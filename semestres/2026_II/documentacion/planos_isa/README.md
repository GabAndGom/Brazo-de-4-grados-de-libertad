# Planos del brazo XK-JS1-1 · versión 2.0 (Kaizen, laboratorio 2)

| Archivo | Contenido |
|---|---|
| `pid/brazo_pid_historico.dwg` | P&ID histórico (sin cambios) |
| `pid/brazo_pid_v2.dwg` / `.dxf` / `.pdf` | P&ID v2.0 · ISA-5.1-2009 · plano P&ID-B4G-01 |
| `electrico/brazo_electrico_historico.dwg` | Plano eléctrico histórico (sin cambios) |
| `electrico/brazo_electrico_v2.dwg` / `.dxf` / `.pdf` | Esquema eléctrico v2.0 · IEC 60617 / 60204-1 · plano E-B4G-01, hoja 1 (potencia) y hoja 2 (mando PLC) |
| [`guia_lectura_planos.pdf`](guia_lectura_planos.pdf) | Guía de lectura de los planos v2.0: explicación zona por zona con recortes ampliados |

En el DWG eléctrico las dos hojas están lado a lado en el espacio modelo (la hoja 2 empieza en x = 450 mm).

## Regenerar

Los genera [`desarrollo/fuentes/documentacion/planos_isa/generar_planos_v2.py`](../../desarrollo/fuentes/documentacion/planos_isa/generar_planos_v2.py) (Python 3; matplotlib solo para el PDF), que escribe en esta carpeta:

```bash
python3 desarrollo/fuentes/documentacion/planos_isa/generar_planos_v2.py
ODAFileConverter entrada/ salida/ ACAD2018 DWG 0 1 "*.dxf"
```

## Correcciones frente al plano histórico

- Entradas verificadas con el PLC en marcha: I0.0 inductivo de la base; I0.1 a I0.4 finales (X atrás/adelante, Y abajo/arriba).
- Tren de pulsos de X e Y compartido: Q0.1 pasa por K1 (Q0.5) al driver X y por K2 (Q0.6) al driver Y.
- Dirección: Q0.2 base, Q0.3 X (0 = adelante), Q0.4 Y (0 = arriba), conectadas a DIR+.
- Garra: Q0.7 acciona directo el solenoide de 24 V (el «K3» del histórico era el propio solenoide; no hay tercer relé).
- Tags ISA-5.1 en los lazos 100 a 104 (los mismos de la base de datos), enlace PPI al gemelo digital y tabla de E/S.

## Notas de cableado

- Comunes de entradas 1M y 2M a +24 V: el sensor NPN de la base y los contactos cierran la entrada a 0 V.
- PUL+ y DIR+ de los drivers desde las salidas a transistor de 24 V del PLC; PUL- y DIR- a 0 V.
- Driver 2M530 de la base con los DIP en la misma posición que los 2M542; relés MY2N-J con bobina en 13-14 y contacto 9-5.
- Finales LS1–LS4 del plano histórico = S11–S14 del plano v2.0.
