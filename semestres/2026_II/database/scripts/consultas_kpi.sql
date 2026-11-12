-- =====================================================================
-- Consultas del dashboard y de control de la base brazo4gdl (II-2026)
-- Cada una responde a un elemento de los mockups del laboratorio 2.
--   psql -d brazo4gdl -f consultas_kpi.sql
-- =====================================================================

-- 1. Estado "En línea": hay un ciclo abierto (sin fin)
SELECT c.id, c.modo, p.nombre AS programa, c.inicio
FROM ciclo_operacion c LEFT JOIN programa_plc p ON p.id = c.programa_id
WHERE c.fin IS NULL
ORDER BY c.inicio DESC
LIMIT 1;

-- 2. Tiempo encendido: horas de uso por día y por modo
SELECT date_trunc('day', inicio) AS dia, modo,
       round(extract(epoch FROM sum(duracion)) / 3600.0, 2) AS horas
FROM v_ciclo
GROUP BY 1, 2
ORDER BY 1 DESC, 2;

-- 3. Ciclos completados: órdenes "iniciar" aceptadas por día
SELECT date_trunc('day', instante) AS dia, count(*) AS ciclos
FROM orden
WHERE tipo = 'iniciar' AND aceptada
GROUP BY 1
ORDER BY 1 DESC;

-- 4. Tren de pulsos: última frecuencia de cada tren (Hz)
SELECT DISTINCT ON (v.tag_isa) v.tag_isa, v.nombre, m.valor AS hz, m.instante
FROM muestra m JOIN variable v ON v.id = m.variable_id
WHERE v.clase = 'MV'
ORDER BY v.tag_isa, m.instante DESC;

-- 5. Bits de dirección y de selección de eje: último estado de Q0.2 a Q0.6
SELECT DISTINCT ON (p.tag_isa) p.direccion, p.tag_isa, p.descripcion, e.valor, e.instante
FROM estado_io e JOIN punto_io p ON p.id = e.punto_id
WHERE p.direccion IN ('Q0.2', 'Q0.3', 'Q0.4', 'Q0.5', 'Q0.6')
ORDER BY p.tag_isa, e.instante DESC;

-- 6. Lecturas de sensores en tiempo real: último estado de I0.0 a I0.4
SELECT DISTINCT ON (p.tag_isa) p.direccion, p.tag_isa, p.descripcion, e.valor, e.instante
FROM estado_io e JOIN punto_io p ON p.id = e.punto_id
WHERE p.direccion IN ('I0.0', 'I0.1', 'I0.2', 'I0.3', 'I0.4')
ORDER BY p.tag_isa, e.instante DESC;

-- 7. Posición actual de los ejes (vista)
SELECT * FROM v_ultima_posicion;

-- 8. Serie de tiempo del carro X en el último ciclo que tiene telemetría, promedio por minuto
SELECT date_trunc('minute', m.instante) AS t, round(avg(m.valor)::numeric, 2) AS x_mm
FROM muestra m JOIN variable v ON v.id = m.variable_id
WHERE v.tag_isa = 'ZI-102'
  AND m.ciclo_id = (SELECT max(ciclo_id) FROM muestra)
GROUP BY 1
ORDER BY 1;

-- 9. Historial de sesiones (últimos 50 intentos)
SELECT s.instante, s.nombre_usado, r.nombre AS rol, s.ip, s.exito, s.fin - s.instante AS duracion
FROM sesion s
LEFT JOIN usuario u ON u.id = s.usuario_id
LEFT JOIN rol r ON r.id = u.rol_id
ORDER BY s.instante DESC
LIMIT 50;

-- 10. Intentos fallidos por IP en el último día (seguridad)
SELECT ip, count(*) AS fallidos
FROM sesion
WHERE NOT exito AND instante > now() - interval '1 day'
GROUP BY ip
HAVING count(*) >= 3
ORDER BY 2 DESC;

-- 11. Alarmas activas en este momento (último evento de cada alarma = activa)
SELECT a.codigo, a.severidad, ult.instante, ult.detalle
FROM (SELECT DISTINCT ON (alarma_id) alarma_id, activa, instante, detalle
      FROM evento_alarma ORDER BY alarma_id, instante DESC) ult
JOIN alarma a ON a.id = ult.alarma_id
WHERE ult.activa
ORDER BY a.severidad DESC, ult.instante;

-- 12. Alarmas por severidad en los últimos 7 días
SELECT a.severidad, a.codigo, count(*) AS veces
FROM evento_alarma e JOIN alarma a ON a.id = e.alarma_id
WHERE e.activa AND e.instante > now() - interval '7 days'
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;

-- 13. Órdenes rechazadas por usuario y motivo
SELECT coalesce(u.nombre, 'PC local') AS usuario, o.motivo, count(*) AS veces
FROM orden o LEFT JOIN usuario u ON u.id = o.usuario_id
WHERE NOT o.aceptada
GROUP BY 1, 2
ORDER BY 3 DESC;

-- 14. Destinos pedidos en cada orden "mover" (reconstruye la fila con un pivote)
SELECT o.id, o.instante,
       max(p.valor) FILTER (WHERE e.codigo = 'Z') AS theta_deg,
       max(p.valor) FILTER (WHERE e.codigo = 'X') AS x_mm,
       max(p.valor) FILTER (WHERE e.codigo = 'Y') AS y_mm
FROM orden o
JOIN orden_parametro p ON p.orden_id = o.id
JOIN eje e ON e.id = p.eje_id
WHERE o.tipo = 'mover'
GROUP BY o.id, o.instante
ORDER BY o.instante DESC;
