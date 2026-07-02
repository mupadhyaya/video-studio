import chromadb
from chromadb.config import Settings

def initialize_database():
    # Establish connection with disk serialization enabled
    client = chromadb.PersistentClient(path="./chroma_data_store")
    
    # Create a collection with explicit distance metrics
    collection = client.get_or_create_collection(
        name="engineering_knowledge_base",
        metadata={"hnsw:space": "cosine"} # Cosine similarity space for embeddings
    )
    print(f"[SUCCESS] Collection '{collection.name}' initialized and persisted successfully.")
    return collection

if __name__ == "__main__":
    kb_collection = initialize_database()