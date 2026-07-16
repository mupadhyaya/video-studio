import os
from llama_index.core import SimpleDirectoryReader, StorageContext
from llama_index.core.indices import MultiModalVectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

client = QdrantClient(":memory:")
text_store = QdrantVectorStore(client=client, collection_name="text_documents")
image_store = QdrantVectorStore(client=client, collection_name="images")