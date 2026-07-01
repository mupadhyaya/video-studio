import numpy as np

def cosine_similarity(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(dot_product / (norm_v1 * norm_v2))

# Database of high-dimensional vector embeddings (Simulated 4-dimensions)
vector_db = {
    "doc_1_AI_models": np.array([0.92, 0.10, 0.05, 0.01]),
    "doc_2_finance_market": np.array([0.02, 0.88, 0.12, 0.15]),
    "doc_3_quantum_physics": np.array([0.08, 0.11, 0.94, 0.22])
}

# User query representing "Deep neural networks and artificial intelligence algorithms"
query_vector = np.array([0.89, 0.14, 0.06, 0.02])

results = {}
for doc_id, emb in vector_db.items():
    similarity = cosine_similarity(query_vector, emb)
    results[doc_id] = similarity

sorted_results = sorted(results.items(), key=lambda item: item[1], reverse=True)

print("=== Vector Database Search Output ===")
for rank, (doc_id, score) in enumerate(sorted_results, 1):
    print(f"Rank {rank}: {doc_id} -> Cosine Similarity: {score:.4f}")