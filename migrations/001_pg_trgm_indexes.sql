-- Migración: Índices pg_trgm para búsquedas ILIKE rápidas
-- Ejecutar contra Neon: psql <DATABASE_URL> -f migrations/001_pg_trgm_indexes.sql

-- Activar extensión (si no está)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Índice para búsquedas por nombre en casos de corrupción
CREATE INDEX IF NOT EXISTS idx_casos_responsable_trgm 
    ON casos_corrupcion USING gin (responsable gin_trgm_ops);

-- Índice para búsquedas por nombre de familiar
CREATE INDEX IF NOT EXISTS idx_familiares_nombre_trgm 
    ON familiares USING gin (nombre_completo gin_trgm_ops);

-- Verificar índices creados
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' AND indexname LIKE '%trgm%'
ORDER BY tablename;
