-- =====================================================================
-- Prueba de las reglas de integridad de brazo4gdl (correr después de brazo_4gdl.sql)
--   psql -d brazo4gdl -f prueba_reglas.sql
-- Todo ocurre dentro de una transacción que se deshace al final: no deja datos.
-- Los valores son de prueba, no mediciones de la planta.
-- =====================================================================
BEGIN;

-- un ciclo de prueba en modo simulación
INSERT INTO ciclo_operacion (sistema_id, programa_id, modo) VALUES (1, 1, 'simulacion');

-- 1. muestra dentro del rango de ZI-102 (0 a 170 mm): entra
INSERT INTO muestra (ciclo_id, variable_id, instante, valor)
SELECT currval('ciclo_operacion_id_seq'), id, now(), 85.0 FROM variable WHERE tag_isa = 'ZI-102';
SELECT 'prueba 1 correcta: muestra en rango aceptada' AS resultado;

-- 2. muestra fuera de rango: el trigger la descarta, registra la alerta y saca la planta de operación
DO $$
DECLARE
    muestras_antes BIGINT;
    alertas_antes  BIGINT;
BEGIN
    SELECT count(*) INTO muestras_antes FROM muestra;
    SELECT count(*) INTO alertas_antes FROM evento_alarma e JOIN alarma a ON a.id = e.alarma_id
        WHERE a.codigo = 'limite_variable';
    INSERT INTO muestra (ciclo_id, variable_id, instante, valor)
    SELECT currval('ciclo_operacion_id_seq'), id, now(), 250.0 FROM variable WHERE tag_isa = 'ZI-102';
    IF (SELECT count(*) FROM muestra) = muestras_antes
       AND (SELECT count(*) FROM evento_alarma e JOIN alarma a ON a.id = e.alarma_id
            WHERE a.codigo = 'limite_variable') = alertas_antes + 1
       AND NOT (SELECT en_operacion FROM sistema WHERE id = 1) THEN
        RAISE NOTICE 'prueba 2 correcta: 250 mm descartado, alerta registrada y planta fuera de operación';
    ELSE
        RAISE NOTICE 'prueba 2 FALLÓ: el trigger no desvió el dato o no registró la alerta';
    END IF;
END $$;

-- 3. valor nulo: NOT NULL lo rechaza
DO $$
BEGIN
    INSERT INTO muestra (ciclo_id, variable_id, instante, valor)
    SELECT currval('ciclo_operacion_id_seq'), id, now(), NULL FROM variable WHERE tag_isa = 'ZI-102';
    RAISE NOTICE 'prueba 3 FALLÓ: se aceptó un valor nulo';
EXCEPTION WHEN not_null_violation THEN
    RAISE NOTICE 'prueba 3 correcta: %', SQLERRM;
END $$;

-- 4. modo inexistente: CHECK lo rechaza
DO $$
BEGIN
    INSERT INTO ciclo_operacion (sistema_id, modo) VALUES (1, 'turbo');
    RAISE NOTICE 'prueba 4 FALLÓ: se aceptó el modo turbo';
EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'prueba 4 correcta: %', SQLERRM;
END $$;

-- 5. variable que no existe: la clave foránea lo rechaza
DO $$
BEGIN
    INSERT INTO muestra (ciclo_id, variable_id, instante, valor)
    VALUES (currval('ciclo_operacion_id_seq'), 999, now(), 1.0);
    RAISE NOTICE 'prueba 5 FALLÓ: se aceptó una variable inexistente';
EXCEPTION WHEN foreign_key_violation THEN
    RAISE NOTICE 'prueba 5 correcta: %', SQLERRM;
END $$;

-- 6. tag ISA repetido: UNIQUE lo rechaza
DO $$
BEGIN
    INSERT INTO punto_io (sistema_id, direccion, tag_isa, tipo_senal, descripcion)
    VALUES (1, 'I1.6', 'ZS-101', 'DI', 'prueba');
    RAISE NOTICE 'prueba 6 FALLÓ: se repitió el tag ZS-101';
EXCEPTION WHEN unique_violation THEN
    RAISE NOTICE 'prueba 6 correcta: %', SQLERRM;
END $$;

-- 7. borrar una variable que ya tiene muestras: ON DELETE RESTRICT lo impide
DO $$
BEGIN
    DELETE FROM variable WHERE tag_isa = 'ZI-102';
    RAISE NOTICE 'prueba 7 FALLÓ: se borró una variable con historial';
EXCEPTION WHEN foreign_key_violation THEN
    RAISE NOTICE 'prueba 7 correcta: %', SQLERRM;
END $$;

ROLLBACK;
