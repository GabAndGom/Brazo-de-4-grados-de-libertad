-- =====================================================================
-- Datos SINTÉTICOS para probar la base brazo4gdl (hito de la fase 2, guía 1:
-- "bases de datos locales creadas, vacías pero probadas con datos sintéticos").
-- NO son mediciones de la planta: trayectorias y eventos generados para ejercitar
-- tablas, índices, trigger, vistas y consultas del dashboard.
--   psql -d brazo4gdl -f datos_sinteticos.sql
-- Para volver a la base vacía: ver el bloque de limpieza al final (comentado).
-- =====================================================================
BEGIN;

-- usuarios de prueba (el hash no corresponde a ninguna contraseña real)
INSERT INTO usuario (nombre, rol_id, clave_hash) VALUES
    ('operador_prueba',   (SELECT id FROM rol WHERE nombre = 'operador'),   'pbkdf2:sintetico:no-es-una-clave'),
    ('observador_prueba', (SELECT id FROM rol WHERE nombre = 'observador'), 'pbkdf2:sintetico:no-es-una-clave');

-- sesiones: dos ingresos correctos y tres fallidos desde la misma IP
INSERT INTO sesion (usuario_id, nombre_usado, ip, instante, exito, fin) VALUES
    ((SELECT id FROM usuario WHERE nombre = 'operador_prueba'),   'operador_prueba',   '192.168.1.50', '2026-11-10 09:00:00-04', true,  '2026-11-10 10:00:00-04'),
    ((SELECT id FROM usuario WHERE nombre = 'observador_prueba'), 'observador_prueba', '192.168.1.51', '2026-11-10 09:05:00-04', true,  '2026-11-10 09:45:00-04'),
    (NULL, 'admin', '192.168.1.99', '2026-11-10 09:10:00-04', false, NULL),
    (NULL, 'admin', '192.168.1.99', '2026-11-10 09:10:20-04', false, NULL),
    (NULL, 'root',  '192.168.1.99', '2026-11-10 09:10:40-04', false, NULL);

-- dos ciclos de operación de una hora: uno en red (cerrado) y uno local (abierto)
INSERT INTO ciclo_operacion (sistema_id, programa_id, modo, inicio, fin) VALUES
    (1, (SELECT id FROM programa_plc WHERE perfil_app = 'gemelo'), 'red',   '2026-11-10 09:00:00-04', '2026-11-10 10:00:00-04'),
    (1, (SELECT id FROM programa_plc WHERE perfil_app = 'gemelo'), 'local', '2026-11-10 11:00:00-04', NULL);

-- telemetría: una muestra por segundo y por variable durante la primera hora (5 x 3600 = 18 000 filas)
-- trayectorias suaves dentro del rango de cada variable
INSERT INTO muestra (ciclo_id, variable_id, instante, valor)
SELECT c.id, v.id, c.inicio + make_interval(secs => s),
       CASE v.tag_isa
            WHEN 'ZI-101' THEN 90 * sin(s / 600.0)                 -- base, ±90°
            WHEN 'ZI-102' THEN 85 + 60 * sin(s / 300.0)            -- carro X, 25 a 145 mm
            WHEN 'ZI-103' THEN 85 + 60 * cos(s / 450.0)            -- carro Y, 25 a 145 mm
            WHEN 'SY-101' THEN CASE WHEN s % 120 < 30 THEN 2500 ELSE 0 END
            WHEN 'SY-100' THEN CASE WHEN s % 90  < 40 THEN 4000 ELSE 0 END
       END
FROM (SELECT id, inicio FROM ciclo_operacion WHERE modo = 'red') c
CROSS JOIN variable v
CROSS JOIN generate_series(0, 3599) s;

-- cambios de señales digitales (flancos)
INSERT INTO estado_io (ciclo_id, punto_id, instante, valor)
SELECT c.id, p.id, c.inicio + make_interval(secs => t), val
FROM (SELECT id, inicio FROM ciclo_operacion WHERE modo = 'red') c
JOIN (VALUES ('I0.5', 0, true), ('I0.1', 5, true), ('I0.1', 20, false), ('I0.3', 25, true), ('I0.3', 40, false),
             ('I0.0', 45, true), ('I0.0', 60, false), ('Q0.5', 70, true), ('Q0.3', 70, false), ('Q0.5', 300, false),
             ('Q0.6', 310, true), ('Q0.4', 310, true), ('Q0.6', 600, false), ('Q0.7', 900, true), ('Q0.7', 1800, false),
             ('I0.2', 2000, true), ('I0.2', 2005, false)) AS e(dir, t, val) ON true
JOIN punto_io p ON p.direccion = e.dir;

-- órdenes: homing, movimientos (con destinos por eje), garra, una rechazada por rol y una fuera de recorrido
WITH c AS (SELECT id, inicio FROM ciclo_operacion WHERE modo = 'red'),
     op AS (SELECT id FROM usuario WHERE nombre = 'operador_prueba'),
     ob AS (SELECT id FROM usuario WHERE nombre = 'observador_prueba')
INSERT INTO orden (ciclo_id, usuario_id, instante, tipo, aceptada, motivo)
SELECT c.id, u, c.inicio + make_interval(secs => t), tipo, ok, motivo
FROM c, (VALUES
    (2,    (SELECT id FROM op), 'homing',  true,  NULL),
    (70,   (SELECT id FROM op), 'mover',   true,  NULL),
    (310,  (SELECT id FROM op), 'mover',   true,  NULL),
    (900,  (SELECT id FROM op), 'garra',   true,  NULL),
    (1000, (SELECT id FROM ob), 'mover',   false, 'su usuario es observador: solo puede ver el brazo'),
    (1200, (SELECT id FROM op), 'mover',   false, 'destino fuera del recorrido'),
    (1500, (SELECT id FROM op), 'iniciar', true,  NULL),
    (2500, (SELECT id FROM op), 'iniciar', true,  NULL),
    (3500, (SELECT id FROM op), 'detener', true,  NULL)) AS o(t, u, tipo, ok, motivo);

INSERT INTO orden_parametro (orden_id, eje_id, valor)
SELECT o.id, e.id, d.valor
FROM (SELECT id, row_number() OVER (ORDER BY instante) AS n FROM orden WHERE tipo = 'mover') o
JOIN (VALUES (1, 'Z', 30.0), (1, 'X', 120.0), (1, 'Y', 40.0), (2, 'X', 60.0), (2, 'Y', 150.0),
             (3, 'X', 100.0), (4, 'X', 250.0)) AS d(n, eje, valor) ON d.n = o.n
JOIN eje e ON e.codigo = d.eje;

-- alarmas: un paro que se normaliza y un destino fuera de rango
INSERT INTO evento_alarma (alarma_id, ciclo_id, instante, activa, detalle)
SELECT a.id, c.id, c.inicio + make_interval(secs => t), act, det
FROM (SELECT id, inicio FROM ciclo_operacion WHERE modo = 'red') c
JOIN (VALUES ('paro', 1300, true, 'pulsador de paro (sintético)'), ('paro', 1400, false, NULL),
             ('fuera_de_rango', 1200, true, 'X = 250 mm pedido (sintético)'), ('fuera_de_rango', 1201, false, NULL),
             ('watchdog', 3550, true, 'sin latido de la PC (sintético)')) AS e(cod, t, act, det) ON true
JOIN alarma a ON a.codigo = e.cod;

COMMIT;
ANALYZE;

-- Limpieza (dejar la base como recién creada):
-- TRUNCATE muestra, estado_io, orden_parametro, orden, evento_alarma, ciclo_operacion, sesion, usuario RESTART IDENTITY;
-- UPDATE sistema SET en_operacion = true;
