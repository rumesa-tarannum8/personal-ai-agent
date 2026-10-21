from typing import Sequence

import numpy as np


class FakeEmbedder:
    """Deterministic bag-of-tokens embedder for tests (no model download)."""

    vocabulary = (
        "peanut",
        "allerg",
        "food",
        "avoid",
        "color",
        "blue",
        "teal",
        "meeting",
        "morning",
    )

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        vectors = [self._vector_for(text) for text in texts]
        return np.vstack(vectors)

    def _vector_for(self, text: str) -> np.ndarray:
        lowered = text.lower()
        vector = np.zeros(len(self.vocabulary), dtype=np.float32)
        for index, token in enumerate(self.vocabulary):
            if token in lowered:
                vector[index] = 1.0
        if float(np.linalg.norm(vector)) == 0.0:
            vector[0] = 0.01
        return vector
