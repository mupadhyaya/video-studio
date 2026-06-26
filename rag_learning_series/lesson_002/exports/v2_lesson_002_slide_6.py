from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter

# 1. Create an 'example.txt' file with some text for testing
# e.g., 'The quick brown fox jumps over the lazy dog. This is a sample document for RAG.'

# 2. Load a simple document
loader = TextLoader("example.txt") 
documents = loader.load()

# 3. Split the document into chunks
text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

# 4. Initialize Embeddings
# Using a small, efficient model suitable for local setup
model_name = "sentence-transformers/all-MiniLM-L6-v2"
model_kwargs = {'device': 'cpu'} # Use 'cuda' if GPU is available
encode_kwargs = {'normalize_embeddings': False}
embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# 5. Create a FAISS vector store from the documents
# This will generate embeddings for each doc chunk and store them
vectorstore = FAISS.from_documents(docs, embeddings)

print("FAISS vector store created successfully with example document!")
# You can now perform a similarity search:
# query = "What is the document about?"
# docs_with_scores = vectorstore.similarity_search_with_score(query)
# print(docs_with_scores)