import sqlite3
from typing import List

import numpy as np

from app.schemas import MemoryHit
from app.services.embeddings import (
    Embedder,
    cosine_similarity,
    embedding_from_bytes,
    embedding_to_bytes,
)
from app.services.memory import get_memory


def store_embedding(
    connection: sqlite3.Connection,
    memory_id: int,
    embedder: Embedder,
) -> None:
    memory = get_memory(connection, memory_id)
    vector = embedder.embed([memory.content])[0]
    connection.execute(
        "UPDATE memories SET embedding = ? WHERE id = ?",
        (embedding_to_bytes(vector), memory_id),
    )
    connection.commit()


def _ensure_approved_embeddings(
    connection: sqlite3.Connection, embedder: Embedder
) -> List[sqlite3.Row]:
    rows = connection.execute(
        """
        SELECT id, content, approved, created_at, updated_at, embedding
        FROM memories
        WHERE approved = 1
        ORDER BY id ASC
        """
    ).fetchall()
    hydrated: List[sqlite3.Row] = []
    for row in rows:
        if row["embedding"] is None:
            store_embedding(connection, row["id"], embedder)
            row = connection.execute(
                """
                SELECT id, content, approved, created_at, updated_at, embedding
                FROM memories
                WHERE id = ?
                """,
                (row["id"],),
            ).fetchone()
        hydrated.append(row)
    return hydrated


def retrieve_approved_memories(
    connection: sqlite3.Connection,
    embedder: Embedder,
    query: str,
    limit: int = 5,
    min_score: float = 0.0,
) -> List[MemoryHit]:
    rows = _ensure_approved_embeddings(connection, embedder)
    if not rows:
        return []

    query_vector = embedder.embed([query.strip()])[0]
    matrix = np.vstack([embedding_from_bytes(row["embedding"]) for row in rows])
    scores = cosine_similarity(query_vector, matrix)

    ranked: List[MemoryHit] = []
    for row, score in zip(rows, scores):
        if score < min_score:
            continue
        ranked.append(
            MemoryHit(
                id=row["id"],
                content=row["content"],
                approved=True,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                score=round(float(score), 6),
            )
        )
    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:limit]
