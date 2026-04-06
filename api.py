import os
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from agent.investigator import run_investigation
from agent.tools import get_relationships, search_entities

load_dotenv()

app = FastAPI()

API_KEY = os.getenv("TRACE_API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(key: str = Security(api_key_header)):
    return key

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://trace-gray.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class InvestigateRequest(BaseModel):
    query: str


@app.post("/investigate")
async def investigate(request: InvestigateRequest, key: str = Security(verify_api_key)):
    report = run_investigation(request.query)

    entities = search_entities(request.query)
    graph_nodes = []
    graph_links = []

    for entity in entities:
        graph_nodes.append({
            "id": entity["id"],
            "name": entity["canonical_name"],
            "type": entity["type"]
        })
        relationships = get_relationships(entity["id"])
        for rel in relationships:
            graph_nodes.append({
                "id": rel["connected_entity_id"],
                "name": rel["connected_entity_name"],
                "type": rel["connected_entity_type"]
            })
            graph_links.append({
                "source": entity["id"],
                "target": rel["connected_entity_id"],
                "label": rel["relationship_type"]
            })

    seen = set()
    unique_nodes = []
    for node in graph_nodes:
        if node["id"] not in seen:
            seen.add(node["id"])
            unique_nodes.append(node)

    return {
        "report": report,
        "graph": {
            "nodes": unique_nodes,
            "links": graph_links
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok"}