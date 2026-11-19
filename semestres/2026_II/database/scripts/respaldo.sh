#!/bin/sh
# Respaldo diario de la base brazo4gdl (guía 8, tarea 63). Guarda los últimos 30 y borra los más viejos.
#   ./respaldo.sh                          -> respaldos/brazo4gdl_AAAA-MM-DD_HHMM.dump
#   crontab -e  y agregar:  0 23 * * * /ruta/a/respaldo.sh >> /ruta/a/respaldos/respaldo.log 2>&1
# Restaurar en una base nueva:  createdb brazo4gdl_restaurada && pg_restore -d brazo4gdl_restaurada ARCHIVO.dump
set -eu
BASE="${BRAZO_BASE:-brazo4gdl}"
DESTINO="${BRAZO_RESPALDOS:-$(dirname "$0")/respaldos}"
CONSERVAR="${BRAZO_CONSERVAR:-30}"
mkdir -p "$DESTINO"
ARCHIVO="$DESTINO/${BASE}_$(date +%Y-%m-%d_%H%M).dump"
pg_dump -Fc -f "$ARCHIVO" "$BASE"
pg_restore -l "$ARCHIVO" > /dev/null          # verifica que el archivo se pueda leer
echo "$(date '+%F %T') respaldo $ARCHIVO ($(du -h "$ARCHIVO" | cut -f1))"
ls -1t "$DESTINO"/"${BASE}"_*.dump | tail -n +"$((CONSERVAR + 1))" | while read -r viejo; do rm -f -- "$viejo"; echo "  borrado $viejo"; done
