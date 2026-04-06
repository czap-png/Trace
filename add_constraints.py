from db.client import get_connection

constraints = [
    "ALTER TABLE entities ADD CONSTRAINT unique_type_name UNIQUE (type, canonical_name)",
    "ALTER TABLE relationships ADD CONSTRAINT unique_relationship UNIQUE (from_entity_id, to_entity_id, relationship_type)",
]

with get_connection() as conn:
    for stmt in constraints:
        try:
            with conn.cursor() as cur:
                cur.execute(stmt)
            conn.commit()
            print(f"OK: {stmt[:60]}")
        except Exception as e:
            conn.rollback()
            print(f"SKIP: {e}")

print("Done")