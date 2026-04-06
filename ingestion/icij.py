import csv
import json
from ingestion.base import BasePipeline

ENTITIES_PATH = "data/icij/nodes-entities.csv"
OFFICERS_PATH = "data/icij/nodes-officers.csv"
MAX_ENTITIES = 5000
MAX_OFFICERS = 5000


class ICIJPipeline(BasePipeline):
    source_name = "icij"

    def fetch(self):
        records = []
        with open(ENTITIES_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= MAX_ENTITIES:
                    break
                records.append({"record_type": "entity", **row})
        with open(OFFICERS_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= MAX_OFFICERS:
                    break
                records.append({"record_type": "officer", **row})
        return records

    def normalise(self, raw):
        results = []
        for record in raw:
            name = record.get("name", "").strip()
            if not name:
                continue
            if record["record_type"] == "entity":
                results.append({
                    "type": "company",
                    "canonical_name": name[:500],
                    "jurisdiction": record.get("jurisdiction_description", ""),
                    "external_ids": {"icij_node_id": record.get("node_id", "")},
                    "metadata": {
                        "source_leak": record.get("sourceID", ""),
                        "service_provider": record.get("service_provider", ""),
                        "status": record.get("status", "")
                    },
                    "risk_flag": {
                        "flag_type": "offshore_leak",
                        "severity": "high",
                        "description": "Appears in " + record.get("sourceID", "ICIJ Offshore Leaks")
                    },
                    "raw": record
                })
            elif record["record_type"] == "officer":
                results.append({
                    "type": "person",
                    "canonical_name": name[:500],
                    "jurisdiction": record.get("countries", ""),
                    "external_ids": {"icij_node_id": record.get("node_id", "")},
                    "metadata": {"source_leak": record.get("sourceID", "")},
                    "risk_flag": {
                        "flag_type": "offshore_leak",
                        "severity": "medium",
                        "description": "Named as officer in " + record.get("sourceID", "ICIJ Offshore Leaks")
                    },
                    "raw": record
                })
        return results

    def upsert(self, conn, normalised):
        with conn.cursor() as cur:
            for record in normalised:
                cur.execute(
                    "INSERT INTO entities (type, canonical_name, jurisdiction, external_ids, metadata) "
                    "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (type, canonical_name) DO NOTHING RETURNING id",
                    (record["type"], record["canonical_name"], record["jurisdiction"],
                     json.dumps(record["external_ids"]), json.dumps(record["metadata"]))
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        "SELECT id FROM entities WHERE type = %s AND canonical_name = %s",
                        (record["type"], record["canonical_name"])
                    )
                    row = cur.fetchone()
                if row is None:
                    continue
                entity_id = row[0]
                cur.execute(
                    "INSERT INTO sources (entity_id, source_name, raw_data) VALUES (%s, %s, %s)",
                    (entity_id, self.source_name, json.dumps(record["raw"]))
                )
                flag = record["risk_flag"]
                cur.execute(
                    "INSERT INTO risk_flags (entity_id, flag_type, severity, description) "
                    "VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (entity_id, flag["flag_type"], flag["severity"], flag["description"])
                )
        conn.commit()
        print(f"[{self.source_name}] Committed to database.")