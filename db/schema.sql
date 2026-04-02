CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE entities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type            TEXT NOT NULL CHECK (type IN ('company', 'person', 'domain', 'address', 'vessel', 'unknown')),
    canonical_name  TEXT NOT NULL,
    aliases         TEXT[],
    jurisdiction    TEXT,
    external_ids    JSONB NOT NULL DEFAULT '{}',
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE relationships (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_entity_id      UUID NOT NULL REFERENCES entities(id),
    to_entity_id        UUID NOT NULL REFERENCES entities(id),
    relationship_type   TEXT NOT NULL,
    start_date          DATE,
    end_date            DATE,
    is_active           BOOLEAN GENERATED ALWAYS AS (end_date IS NULL) STORED,
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id       UUID REFERENCES entities(id),
    relationship_id UUID REFERENCES relationships(id),
    source_name     TEXT NOT NULL,
    source_url      TEXT,
    raw_data        JSONB NOT NULL DEFAULT '{}',
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (entity_id IS NOT NULL OR relationship_id IS NOT NULL)
);

CREATE TABLE risk_flags (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id   UUID NOT NULL REFERENCES entities(id),
    flag_type   TEXT NOT NULL,
    severity    TEXT CHECK (severity IN ('high', 'medium', 'low', 'informational')),
    description TEXT,
    source_id   UUID REFERENCES sources(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_canonical_name ON entities(canonical_name);
CREATE INDEX idx_entities_external_ids ON entities USING gin(external_ids);
CREATE INDEX idx_relationships_from ON relationships(from_entity_id);
CREATE INDEX idx_relationships_to ON relationships(to_entity_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);
CREATE INDEX idx_risk_flags_entity ON risk_flags(entity_id);
CREATE INDEX idx_risk_flags_type ON risk_flags(flag_type);
CREATE INDEX idx_sources_entity ON sources(entity_id);
CREATE INDEX idx_sources_name ON sources(source_name);

ALTER TABLE entities ADD CONSTRAINT unique_type_name UNIQUE (type, canonical_name);
ALTER TABLE relationships ADD CONSTRAINT unique_relationship UNIQUE (from_entity_id, to_entity_id, relationship_type);