def run_semantic_query(collection):
    # Retrieve relevant contexts using query texts matched with metadata filters
    query_results = collection.query(
        query_texts=["How can I resolve slow performance bottleneck issues?"],
        n_results=1,
        where={"tier": "backend"} # Metadata filter constraint
    )
    
    print("\n[QUERY OUTPUT]")
    for idx, doc in enumerate(query_results['documents'][0]):
        dist = query_results['distances'][0][idx]
        meta = query_results['metadatas'][0][idx]
        print(f"Document: {doc}\nDistance: {dist}\nMetadata: {meta}\n")