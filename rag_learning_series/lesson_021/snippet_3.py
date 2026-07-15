import uuid
import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction

# Initialize high-performance ChromaDB client
client = chromadb.PersistentClient(path="./multimodal_rag_db")

# OpenCLIP handles both text and image embeddings in a shared space
clip_ef = OpenCLIPEmbeddingFunction()
multimodal_collection = client.get_or_create_collection(
    name="enterprise_multimodal_rag", 
    embedding_function=clip_ef
)

# Function to index raw document images and their summaries
def index_multimodal_element(image_path, text_summary, metadata):
    doc_id = str(uuid.uuid4())
    
    # Store the text summary referencing the raw visual artifact ID
    multimodal_collection.add(
        ids=[f"{doc_id}_summary"],
        documents=[text_summary],
        metadatas=[{**metadata, "type": "summary", "parent_id": doc_id}]
    )
    
    # Store the raw image itself under the same parent ID 
    # OpenCLIP embedding function automatically reads image paths from URIs
    multimodal_collection.add(
        ids=[f"{doc_id}_image"],
        uris=[image_path],
        metadatas=[{**metadata, "type": "image", "parent_id": doc_id}]
    )
    print(f"Successfully indexed multi-modal entity ID: {doc_id}")