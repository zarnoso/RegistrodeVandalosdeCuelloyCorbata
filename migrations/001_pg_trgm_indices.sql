-- Migración: índices pg_trgm para búsqueda por texto libre (ILIKE '%x%')
-- Aplicado directamente en Neon el 2026-09-03 (commit dd36221).
-- Este script documenta lo ya ejecutado y sirve para reproducirlo en otro
-- entorno (staging, otra instancia) si hace falta. Es idempotente:
-- IF NOT EXISTS evita error si ya existe.

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- casos_corrupcion.responsable: usado con ILIKE '%nombre%' en listar_politicos,
-- grafo, som, buscar_por_alias y detalle_politico. Sin índice trigram, cada uno
-- de esos queries hace un full table scan por cada político.
CREATE INDEX IF NOT EXISTS idx_casos_responsable_trgm
    ON casos_corrupcion USING gin (responsable gin_trgm_ops);

-- familiares.nombre_completo: usado con ILIKE en el cálculo de riesgo heredado
-- y en la búsqueda de casos de cada familiar (detalle_politico).
CREATE INDEX IF NOT EXISTS idx_familiares_nombre_trgm
    ON familiares USING gin (nombre_completo gin_trgm_ops);

-- politicos.nombre_completo: usado en el JOIN de listar_politicos/grafo/som
-- contra casos_corrupcion.responsable.
CREATE INDEX IF NOT EXISTS idx_politicos_nombre_trgm
    ON politicos USING gin (nombre_completo gin_trgm_ops);

-- Verificación (ejecutar aparte, no es parte de la migración):
-- SELECT indexname, tablename FROM pg_indexes WHERE indexname LIKE '%_trgm';
