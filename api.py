from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent.investigator import run_investigation
from agent.tools import get_relationships, search_entities

app = FastAPI()

# Allow the React frontend to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class InvestigateRequest(BaseModel):
    query: str


@app.post("/investigate")
async def investigate(request: InvestigateRequest):
    """
    Run a full investigation and return the report and graph data.
    """
    report = run_investigation(request.query)

    # Also fetch the graph data — entities and relationships
    # so the frontend can draw the network diagram
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

    # Remove duplicate nodes
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