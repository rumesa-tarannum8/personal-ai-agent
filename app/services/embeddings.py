from typing import Protocol, Sequence

import numpy as np


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> np.ndarray:
        """Return a 2D float32 array of shape (len(texts), dim)."""


class SentenceTransformerEmbedder:
    """Production embedder. The model is loaded on first use."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        vectors = self._model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=False,
        )
        return np.asarray(vectors, dtype=np.float32)


def cosine_similarity(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Cosine similarity between a 1D query vector and a 2D matrix of vectors."""
    query = np.asarray(query, dtype=np.float64).reshape(-1)
    matrix = np.asarray(matrix, dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError("matrix must be 2-dimensional")
    query_norm = np.linalg.norm(query)
    row_norms = np.linalg.norm(matrix, axis=1)
    denominators = query_norm * row_norms
    dots = matrix @ query
    scores = np.zeros(matrix.shape[0], dtype=np.float64)
    nonzero = denominators > 0
    scores[nonzero] = dots[nonzero] / denominators[nonzero]
    return scores


def embedding_to_bytes(vector: np.ndarray) -> bytes:
    return np.asarray(vector, dtype=np.float32).tobytes()


def embedding_from_bytes(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32).copy()
