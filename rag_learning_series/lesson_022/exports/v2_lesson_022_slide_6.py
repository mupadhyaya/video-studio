import uuid
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# Initialize vector DB and in-memory key-value storage
vectorstore = Chroma(
    collection_name="multimodal_rag_store", 
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small")
)

image_document_store = {}

def index_multimodal_element(summary_data, raw_base64_image):
    """Indexes summary vector inside Chroma, and raw image within document store."""
    element_id = str(uuid.uuid4())
    
    # Document structure for Vector Store
    summary_document = Document(
        page_content=summary_data["summary"],
        metadata={
            "element_id": element_id,
            "metrics": json.dumps(summary_data["extracted_metrics"]),
            "type": "image"
        }
    )
    
    # Add to database stores
    vectorstore.add_documents([summary_document], ids=[element_id])
    image_document_store[element_id] = raw_base64_image
    
    return element_id