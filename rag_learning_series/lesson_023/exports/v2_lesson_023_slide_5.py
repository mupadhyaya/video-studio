from pydantic import BaseModel, Field
from typing import List, Dict, Any
import json

class Entity(BaseModel):
    id: str = Field(..., description="Unique identifier for the node, typically the name.")
    type: str = Field(..., description="The category of the entity (e.g., Person, Org, Technology)")
    description: str = Field(..., description="A comprehensive summary of the entity's attributes.")

class Relationship(BaseModel):
    source: str = Field(..., description="Source entity ID representing the starting node.")
    target: str = Field(..., description="Target entity ID representing the ending node.")
    description: str = Field(..., description="A clear explanation of how the source and target are linked.")
    weight: float = Field(1.0, description="Strength of the connection based on frequency of occurrence.")

class CommunityCluster(BaseModel):
    cluster_id: int
    entities: List[str]
    relationships: List[Dict[str, str]]
    community_summary: str

# Dynamic mock database router
def run_graph_routing(query: str, communities: List[CommunityCluster]) -> str:
    print(f"[Router] Processing global query: '{query}'")
    matching_summaries = []
    for community in communities:
        if any(entity.lower() in query.lower() for entity in community.entities):
            print(f"[Router] Matching community found: Cluster {community.cluster_id}")
            matching_summaries.append(community.community_summary)
    
    return "\n\n".join(matching_summaries) if matching_summaries else "Default Global Context Not Found."