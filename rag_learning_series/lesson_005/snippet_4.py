import numpy as np
from typing import List

class SemanticSimilarityCalculator:
    """Calculates exact cosine similarity between raw mathematical vectors."""
    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        return float(dot_product / (norm_v1 * norm_v2))

# Example vectors representing conceptual semantic coordinates
# Dimensions [Royalty, Masculinity, Femininity, Plant-Life]
king = np.array([0.95, 0.90, 0.05, 0.00])
queen = np.array([0.95, 0.05, 0.90, 0.00])
apple = np.array([0.00, 0.00, 0.00, 0.98])

sim_king_queen = SemanticSimilarityCalculator.cosine_similarity(king, queen)
sim_king_apple = SemanticSimilarityCalculator.cosine_similarity(king, apple)

print(f"Similarity (King, Queen): {sim_king_queen:.4f}")
print(f"Similarity (King, Apple): {sim_king_apple:.4f}")