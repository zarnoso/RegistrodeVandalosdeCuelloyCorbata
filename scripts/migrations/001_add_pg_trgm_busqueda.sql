-- Migración: búsqueda tolerante a typos/tildes por nombre_completo
-- No rompe funcionalidad existente: solo agrega extensión + índice.
-- Ejecutar: psql $DATABASE_URL -f scripts/migrations/001_add_pg_trgm_busqueda.sql

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- unaccent() es STABLE y PostgreSQL no permite usarla directamente en un
-- índice de expresión. Este wrapper fijo permite indexar el texto normalizado.
CREATE OR REPLACE FUNCTION immutable_unaccent(text)
RETURNS text
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
STRICT
AS $$
    SELECT public.unaccent('public.unaccent'::regdictionary, $1)
$$;

CREATE INDEX IF NOT EXISTS idx_politicos_nombre_trgm
    ON politicos USING gin (
        immutable_unaccent(lower(nombre_completo)) gin_trgm_ops
    );
