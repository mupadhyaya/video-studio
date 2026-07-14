from mcp.server.fastmcp import FastMCP
from qdrant_client import QdrantClient

# Initialize FastMCP Server and Qdrant Client
mcp = FastMCP("qdrant-vector-service")
qdrant_db = QdrantClient(url="http://localhost:6333")

@mcp.tool()
def query_vectors(collection_name: str, query_text: str, limit: int = 3) -> str:
    """
    Perform a semantic similarity search across the specified vector database collection.
    
    Args:
        collection_name (str): The name of the target database collection.
        query_text (str): The search query context.
        limit (int): Max number of highly relevant records to retrieve.
    """
    try:
        results = qdrant_db.query(
            collection_name=collection_name,
            query_text=query_text,
            limit=limit
        )
        payloads = [str(r.metadata) for r in results]
        return "\n".join(payloads) if payloads else "No relevant documentation found."
    except Exception as e:
        return f"Database query failed with error: {str(e)}"