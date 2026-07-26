-- Relaciones familiares/empresariales y trazabilidad de antecedentes.
-- Aplicar después de 001_add_pg_trgm_busqueda.sql.

ALTER TABLE eventos
    ADD COLUMN IF NOT EXISTS url_oficial TEXT,
    ADD COLUMN IF NOT EXISTS rit_ruc VARCHAR(100),
    ADD COLUMN IF NOT EXISTS tribunal VARCHAR(255),
    ADD COLUMN IF NOT EXISTS fecha_verificacion TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE familiares
    ADD COLUMN IF NOT EXISTS fuente VARCHAR(100),
    ADD COLUMN IF NOT EXISTS url_fuente TEXT,
    ADD COLUMN IF NOT EXISTS verificada_humano BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

CREATE TABLE IF NOT EXISTS familiares_empresas (
    id UUID PRIMARY KEY,
    familiar_id UUID NOT NULL
        REFERENCES familiares(id) ON DELETE CASCADE,
    empresa_id UUID NOT NULL
        REFERENCES empresas(id) ON DELETE CASCADE,
    rol_familiar VARCHAR(100),
    vinculo_politico VARCHAR(255),
    fuente VARCHAR(100),
    url_fuente TEXT,
    verificada_humano BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_familiar_empresa UNIQUE (familiar_id, empresa_id)
);

CREATE INDEX IF NOT EXISTS idx_eventos_politico_fecha
    ON eventos (politico_id, fecha_inicio DESC);
CREATE INDEX IF NOT EXISTS idx_eventos_estado
    ON eventos (estado_actual);
CREATE INDEX IF NOT EXISTS idx_patrimonio_politico
    ON patrimonio (politico_id);
CREATE INDEX IF NOT EXISTS idx_empresas_patrimonio
    ON empresas (patrimonio_id);
CREATE INDEX IF NOT EXISTS idx_familiares_politico
    ON familiares (politico_id);
CREATE INDEX IF NOT EXISTS idx_familiares_empresas_familiar
    ON familiares_empresas (familiar_id);
CREATE INDEX IF NOT EXISTS idx_familiares_empresas_empresa
    ON familiares_empresas (empresa_id);
