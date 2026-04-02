import json
from ingestion.base import BasePipeline

DATA_PATH = "data/opensanctions.json"

class OpenSanctionsPipeline(BasePipeline):
    source_name = "open_sanctions"

    def fetch(self) -> list:
        """
        Read the bulk download file line by line.
        Each line is a separate JSON object representing one entity.
        We only keep people and companies for now.
        """
        records = []
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entity = json.loads(line)
                except json.JSONDecodeError:
                    continue
                schema = entity.get("schema", "")
                if schema in ("Person", "Company", "Organization", "LegalEntity"):
                    records.append(entity)
                if len(records) >= 1000:
                    # Cap at 1000 for now so our first run is fast.
                    # We'll remove this limit later.
                    break
        return records

    def normalise(self, raw: list) -> list:
        results = []
        for entity in raw:
            schema = entity.get("schema", "")
            props = entity.get("properties", {})

            # Map OpenSanctions schema types to our entity types
            if schema == "Person":
                entity_type = "person"
            elif schema in ("Company", "Organization", "LegalEntity"):
                entity_type = "company"
            else:
                entity_type = "unknown"

            # OpenSanctions stores names as a list — take the first one
            names = props.get("name", [])
            if not names:
                continue
            canonical_name = names[0][:500]  # safety truncation

            # Jurisdiction comes from the country field
            countries = props.get("country", [])
            jurisdiction = countries[0] if countries else None

            results.append({
                "type": entity_type,
                "canonical_name": canonical_name,
                "jurisdiction": jurisdiction,
                "external_ids": {"open_sanctions": entity.get("id", "")},
                "metadata": {
                    "aliases": names[1:],
                    "topics": props.get("topics", []),
                    "nationalities": props.get("nationality", [])
                },
                "risk_flag": {
                    "flag_type": "sanctions",
                    "severity": "high",
                    "description": f"Listed in OpenSanctions. Topics: {', '.join(props.get('topics', []))}"
                },
                "raw": entity
            })
        return results

    def upsert(self, conn, normalised: list):
        with conn.cursor() as cur:
            for record in normalised:
                # Upsert the entity
                cur.execute("""
                    INSERT INTO entities
                        (type, canonical_name, jurisdiction, external_ids, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (type, canonical_name) DO NOTHING
                    RETURNING id
                """, (
                    record["type"],
                    record["canonical_name"],
                    record["jurisdiction"],
                    json.dumps(record["external_ids"]),
                    json.dumps(record["metadata"])
                ))
                row = cur.fetchone()

                if row is None:
                    cur.execute("""
                        SELECT id FROM entities
                        WHERE type = %s AND canonical_name = %s
                    """, (record["type"], record["canonical_name"]))
                    row = cur.fetchone()

                if row is None:
                    continue

                entity_id = row[0]

                # Write provenance
                cur.execute("""
                    INSERT INTO sources (entity_id, source_name, raw_data)
                    VALUES (%s, %s, %s)
                """, (entity_id, self.source_name, json.dumps(record["raw"])))

                # Write risk flag
                flag = record["risk_flag"]
                cur.execute("""
                    INSERT INTO risk_flags
                        (entity_id, flag_type, severity, description)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    entity_id,
                    flag["flag_type"],
                    flag["severity"],
                    flag["description"]
                ))

            conn.commit()
            print(f"[{self.source_name}] Committed to database.")