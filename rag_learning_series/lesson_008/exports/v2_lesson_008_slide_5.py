def ingest_batch_documents(collection):
    # Prepare highly granular records with rich metadata
    documents = [
        "In memory caching with Redis dramatically optimizes high-load microservice response times.",
        "PostgreSQL indexes can be optimized using partial index structures on frequently accessed keys.",
        "ChromaDB provides fast nearest neighbor searches using hierarchical navigable small world trees."
    ]
    
    metadatas = [
        {"module": "caching", "tier": "backend", "priority": "critical"},
        {"module": "database", "tier": "backend", "priority": "medium"},
        {"module": "vector_db", "tier": "infrastructure", "priority": "high"}
    ]
    
    ids = ["doc_redis_001", "doc_pg_002", "doc_chroma_003"]
    
    # Ingest the payload into our persistent collection
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print("[SUCCESS] Ingestion completed. Documents successfully indexed.")