import uuid
from typing import List, Dict, Any

class HybridMemoryOrchestrator:
    def __init__(self, vector_db_client, embedding_model, window_size: int = 5):
        self.vector_db = vector_db_client
        self.embedding_model = embedding_model
        self.window_size = window_size
        self.short_term_buffer: List[Dict[str, str]] = []

    def add_interaction(self, user_query: str, system_response: str):
        # Save to immediate sliding memory window
        self.short_term_buffer.append({"user": user_query, "system": system_response})
        if len(self.short_term_buffer) > self.window_size:
            self.short_term_buffer.pop(0)
        
        # Persist to Semantic Vector Database
        combined_text = f"User: {user_query} | System: {system_response}"
        embedding = self.embedding_model.embed_query(combined_text)
        self.vector_db.add(
            ids=[str(uuid.uuid4())],
            embeddings=[embedding],
            documents=[combined_text]
        )

    def get_context(self, current_query: str) -> Dict[str, Any]:
        query_vector = self.embedding_model.embed_query(current_query)
        long_term_hits = self.vector_db.query(query_embeddings=[query_vector], n_results=3)
        return {
            "short_term": self.short_term_buffer,
            "long_term": long_term_hits['documents']
        }