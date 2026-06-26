from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 1. Load and split documents
documents = [
    "Retrieval Augmented Generation (RAG) combines information retrieval with language model generation.",
    "RAG helps LLMs provide more accurate and up-to-date information by grounding responses in external knowledge sources.",
    "Vector databases are crucial for efficient similarity search in RAG systems."
]
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = text_splitter.create_documents([{'page_content': doc} for doc in documents])

# 2. Create embeddings and vector store
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = FAISS.from_documents(chunks, embeddings)
retriever = vector_store.as_retriever()

# 3. Define prompt and LLM
prompt = ChatPromptTemplate.from_template(
    "Answer the following question based only on the provided context:\nContext: {context}\nQuestion: {input}"
)
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0) # Use your OpenAI key or local LLM

# 4. Create RAG chain
document_chain = create_stuff_documents_chain(llm, prompt)
retrieval_chain = create_retrieval_chain(retriever, document_chain)

# 5. Invoke the chain
response = retrieval_chain.invoke({"input": "What is RAG?"})
print(response["answer"])