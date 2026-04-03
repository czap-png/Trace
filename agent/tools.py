import json
from db.client import get_connection
from db.embeddings import search_documents


def search_entities(name: str) -> list:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, type, canonical_name, jurisdiction, metadata
                FROM entities
                WHERE canonical_name ILIKE %s
                LIMIT 10
            """, (f"%{name}%",))
            rows = cur.fetchall()
            return [
                {
                    "id": str(row[0]),
                    "type": row[1],
                    "canonical_name": row[2],
                    "jurisdiction": row[3],
                    "metadata": row[4]
                }
                for row in rows
            ]


def get_relationships(entity_id: str) -> list:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    r.relationship_type,
                    r.start_date,
                    r.end_date,
                    r.is_active,
                    e.canonical_name,
                    e.type,
                    e.id
                FROM relationships r
                JOIN entities e ON (
                    CASE
                        WHEN r.from_entity_id = %s THEN r.to_entity_id
                        ELSE r.from_entity_id
                    END = e.id
                )
                WHERE r.from_entity_id = %s OR r.to_entity_id = %s
            """, (entity_id, entity_id, entity_id))
            rows = cur.fetchall()
            return [
                {
                    "relationship_type": row[0],
                    "start_date": str(row[1]) if row[1] else None,
                    "end_date": str(row[2]) if row[2] else None,
                    "is_active": row[3],
                    "connected_entity_name": row[4],
                    "connected_entity_type": row[5],
                    "connected_entity_id": str(row[6])
                }
                for row in rows
            ]


def get_risk_flags(entity_id: str) -> list:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT flag_type, severity, description, created_at
                FROM risk_flags
                WHERE entity_id = %s
            """, (entity_id,))
            rows = cur.fetchall()
            return [
                {
                    "flag_type": row[0],
                    "severity": row[1],
                    "description": row[2],
                    "created_at": str(row[3])
                }
                for row in rows
            ]


def search_documents_tool(query: str) -> list:
    results = search_documents(query, limit=3)
    return [
        {
            "content": row[0],
            "source": row[1],
            "title": row[2],
            "entity_name": row[3],
            "similarity": float(row[4])
        }
        for row in results
    ]


TOOL_DEFINITIONS = [
    {
        "name": "search_entities",
        "description": "Search for companies or people in the database by name. Use this first to find an entity before looking up their details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name to search for"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "get_relationships",
        "description": "Get all known relationships for an entity — directorships, ownership, connections to other companies or people.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The UUID of the entity to look up"
                }
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_risk_flags",
        "description": "Get sanctions, PEP flags, and other risk signals for an entity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The UUID of the entity to look up"
                }
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "search_documents",
        "description": "Search unstructured documents like news articles and court filings using natural language.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query"
                }
            },
            "required": ["query"]
        }
    }
]

TOOL_FUNCTIONS = {
    "search_entities": search_entities,
    "get_relationships": get_relationships,
    "get_risk_flags": get_risk_flags,
    "search_documents": search_documents_tool,
}