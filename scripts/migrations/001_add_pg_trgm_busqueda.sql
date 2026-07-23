-- Migración: búsqueda tolerante a typos/tildes por nombre_completo
-- No rompe funcionalidad existente: solo agrega extensión + índice.
-- Ejecutar: psql $DATABASE_URL -f scripts/migrations/001_add_pg_trgm_busqueda.sql

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE INDEX IF NOT EXISTS idx_politicos_nombre_trgm
    ON politicos USING gin (nombre_completo gin_trgm_ops);
