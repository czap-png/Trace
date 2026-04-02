import json
from ingestion.base import BasePipeline

MOCK_COMPANIES = [
    {
        "company_number": "12345678",
        "company_name": "ACME HOLDINGS LIMITED",
        "company_status": "active",
        "jurisdiction": "england-wales",
        "registered_office_address": {
            "address_line_1": "123 Fake Street",
            "locality": "London",
            "postal_code": "EC1A 1BB"
        },
        "officers": [
            {
                "name": "SMITH, John David",
                "officer_role": "director",
                "appointed_on": "2020-01-15",
                "resigned_on": None
            },
            {
                "name": "JONES, Sarah",
                "officer_role": "secretary",
                "appointed_on": "2020-01-15",
                "resigned_on": "2022-06-01"
            }
        ]
    },
    {
        "company_number": "87654321",
        "company_name": "JONES VENTURES LTD",
        "company_status": "active",
        "jurisdiction": "england-wales",
        "registered_office_address": {
            "address_line_1": "456 Example Road",
            "locality": "Manchester",
            "postal_code": "M1 1AE"
        },
        "officers": [
            {
                "name": "JONES, Sarah",
                "officer_role": "director",
                "appointed_on": "2021-03-10",
                "resigned_on": None
            }
        ]
    }
]


class CompaniesHousePipeline(BasePipeline):
    source_name = "companies_house"

    def fetch(self) -> list:
        return MOCK_COMPANIES

    def normalise(self, raw: list) -> list:
        results = []
        for company in raw:
            results.append({
                "type": "company",
                "canonical_name": company["company_name"],
                "jurisdiction": company["jurisdiction"],
                "external_ids": {"companies_house": company["company_number"]},
                "metadata": {
                    "status": company["company_status"],
                    "address": company["registered_office_address"]
                },
                "officers": [
                    {
                        "name": o["name"],
                        "role": o["officer_role"],
                        "appointed_on": o["appointed_on"],
                        "resigned_on": o["resigned_on"]
                    }
                    for o in company.get("officers", [])
                ],
                "raw": company
            })
        return results

    def upsert(self, conn, normalised: list):
        with conn.cursor() as cur:
            for record in normalised:
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
                        WHERE external_ids->>'companies_house' = %s
                    """, (record["external_ids"]["companies_house"],))
                    row = cur.fetchone()

                company_id = row[0]

                cur.execute("""
                    INSERT INTO sources (entity_id, source_name, raw_data)
                    VALUES (%s, %s, %s)
                """, (company_id, self.source_name, json.dumps(record["raw"])))

                for officer in record["officers"]:
                    cur.execute("""
                        INSERT INTO entities (type, canonical_name)
                        VALUES (%s, %s)
                        ON CONFLICT (type, canonical_name) DO NOTHING
                        RETURNING id
                    """, ("person", officer["name"]))
                    officer_row = cur.fetchone()

                    if officer_row is None:
                        cur.execute("""
                            SELECT id FROM entities
                            WHERE type = 'person' AND canonical_name = %s
                        """, (officer["name"],))
                        officer_row = cur.fetchone()

                    officer_id = officer_row[0]

                    cur.execute("""
                        INSERT INTO relationships
                            (from_entity_id, to_entity_id, relationship_type,
                             start_date, end_date)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        officer_id,
                        company_id,
                        officer["role"],
                        officer["appointed_on"],
                        officer["resigned_on"]
                    ))

            conn.commit()
            print(f"[{self.source_name}] Committed to database.")