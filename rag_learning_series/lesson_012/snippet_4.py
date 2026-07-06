import logging
from typing import List
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG_Pipeline")

def fetch_context_resilient(query: str, retriever: VectorStoreRetriever) -> List[Document]:
    try:
        # Primary Retrieval Attempt
        logger.info("Attempting primary vector-based retrieval...")
        return retriever.invoke(query)
    except Exception as e:
        # Graceful fallback handler
        logger.critical(f"Primary retrieval database is unreachable: {str(e)}")
        logger.warning("Triggering local static backup context fallback...")
        
        fallback_doc = Document(
            page_content="CRITICAL ERROR: Vector Store Offline. Please fallback to cache or standard operations manual.",
            metadata={"source": "system_fallback", "status": "degraded"}
        )
        return [fallback_doc]