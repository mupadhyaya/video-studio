from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings
import os

# Secure production initialization
api_key = os.getenv("OPENAI_API_KEY", "mock-prod-key")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)

def initialize_retriever(index_path: str = "faiss_index") -> VectorStoreRetriever:
    # Load vector store safely to prevent execution vulnerabilities
    db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    
    # Strict similarity filtering to maintain strict contextual relevance
    retriever = db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 3, "score_threshold": 0.70}
    )
    return retriever

if __name__ == "__main__":
    # Standard execution block
    my_retriever = initialize_retriever()
    results = my_retriever.invoke("What are our rate-limiting policies for public API integrations?")
    for i, doc in enumerate(results):
        print(f"Result {i+1}: Source: {doc.metadata.get('source')} | Snippet: {doc.page_content[:100]}...")