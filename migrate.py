from db.client import get_connection

statements = [
    """CREATE TABLE IF NOT EXISTS entities (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        type TEXT NOT NULL CHECK (type IN ('company', 'person', 'domain', 'address', 'vessel', 'unknown')),
        canonical_name TEXT NOT NULL,
        aliases TEXT[],
        jurisdiction TEXT,
        external_ids JSONB NOT NULL DEFAULT '{}',
        metadata JSONB NOT NULL DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS relationships (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        from_entity_id UUID NOT NULL REFERENCES entities(id),
        to_entity_id UUID NOT NULL REFERENCES entities(id),
        relationship_type TEXT NOT NULL,
        start_date DATE,
        end_date DATE,
        is_active BOOLEAN GENERATED ALWAYS AS (end_date IS NULL) STORED,
        metadata JSONB NOT NULL DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS sources (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        entity_id UUID REFERENCES entities(id),
        relationship_id UUID REFERENCES relationships(id),
        source_name TEXT NOT NULL,
        source_url TEXT,
        raw_data JSONB NOT NULL DEFAULT '{}',
        fetched_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS risk_flags (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        entity_id UUID NOT NULL REFERENCES entities(id),
        flag_type TEXT NOT NULL,
        severity TEXT CHECK (severity IN ('high', 'medium', 'low', 'informational')),
        description TEXT,
        source_id UUID REFERENCES sources(id),
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS documents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        entity_id UUID REFERENCES entities(id),
        source_name TEXT NOT NULL,
        source_url TEXT,
        title TEXT,
        content TEXT NOT NULL,
        chunk_index INTEGER NOT NULL DEFAULT 0,
        embedding vector(1536),
        metadata JSONB NOT NULL DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    "CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)",
    "CREATE INDEX IF NOT EXISTS idx_entities_canonical_name ON entities(canonical_name)",
    "CREATE INDEX IF NOT EXISTS idx_entities_external_ids ON entities USING gin(external_ids)",
    "CREATE INDEX IF NOT EXISTS idx_relationships_from ON relationships(from_entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_relationships_to ON relationships(to_entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type)",
    "CREATE INDEX IF NOT EXISTS idx_risk_flags_entity ON risk_flags(entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_risk_flags_type ON risk_flags(flag_type)",
    "CREATE INDEX IF NOT EXISTS idx_sources_entity ON sources(entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_sources_name ON sources(source_name)",
    "ALTER TABLE entities ADD CONSTRAINT IF NOT EXISTS unique_type_name UNIQUE (type, canonical_name)",
    "ALTER TABLE relationships ADD CONSTRAINT IF NOT EXISTS unique_relationship UNIQUE (from_entity_id, to_entity_id, relationship_type)",
]

with get_connection() as conn:
    for stmt in statements:
        try:
            with conn.cursor() as cur:
                cur.execute(stmt)
            conn.commit()
            print(f"OK: {stmt[:60]}...")
        except Exception as e:
            conn.rollback()
            print(f"SKIP: {e}")

print("Migration complete")