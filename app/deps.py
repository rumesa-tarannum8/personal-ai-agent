import sqlite3

from fastapi import Request

from app.services.embeddings import Embedder, SentenceTransformerEmbedder


def get_connection(request: Request) -> sqlite3.Connection:
    return request.app.state.db


def get_embedder(request: Request) -> Embedder:
    embedder = getattr(request.app.state, "embedder", None)
    if embedder is None:
        embedder = SentenceTransformerEmbedder(
            request.app.state.settings.embedding_model
        )
        request.app.state.embedder = embedder
    return embedder
