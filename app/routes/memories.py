import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status

from app.deps import get_connection, get_embedder
from app.schemas import (
    MemoryCreate,
    MemoryListOut,
    MemoryOut,
    MemoryRetrieveOut,
    MemoryUpdate,
)
from app.services import memory as memory_service
from app.services.embeddings import Embedder
from app.services import retrieval as retrieval_service

router = APIRouter(prefix="/memories", tags=["memories"])


@router.post("", response_model=MemoryOut, status_code=status.HTTP_201_CREATED)
def create_memory(
    payload: MemoryCreate,
    connection: sqlite3.Connection = Depends(get_connection),
) -> MemoryOut:
    return memory_service.create_memory(connection, payload.content)


@router.get("", response_model=MemoryListOut)
def list_memories(
    approved: Optional[bool] = Query(default=None),
    connection: sqlite3.Connection = Depends(get_connection),
) -> MemoryListOut:
    return MemoryListOut(items=memory_service.list_memories(connection, approved))


@router.get("/search", response_model=MemoryListOut)
def search_memories(
    q: str = Query(..., min_length=1, max_length=400),
    approved: Optional[bool] = Query(default=None),
    connection: sqlite3.Connection = Depends(get_connection),
) -> MemoryListOut:
    return MemoryListOut(items=memory_service.search_memories(connection, q, approved))


@router.get("/retrieve", response_model=MemoryRetrieveOut)
def retrieve_memories(
    q: str = Query(..., min_length=1, max_length=400),
    limit: int = Query(default=5, ge=1, le=50),
    min_score: float = Query(default=0.0, ge=-1.0, le=1.0),
    connection: sqlite3.Connection = Depends(get_connection),
    embedder: Embedder = Depends(get_embedder),
) -> MemoryRetrieveOut:
    return MemoryRetrieveOut(
        items=retrieval_service.retrieve_approved_memories(
            connection,
            embedder,
            q,
            limit=limit,
            min_score=min_score,
        )
    )


@router.get("/{memory_id}", response_model=MemoryOut)
def get_memory(
    memory_id: int,
    connection: sqlite3.Connection = Depends(get_connection),
) -> MemoryOut:
    return memory_service.get_memory(connection, memory_id)


@router.patch("/{memory_id}", response_model=MemoryOut)
def update_memory(
    memory_id: int,
    payload: MemoryUpdate,
    connection: sqlite3.Connection = Depends(get_connection),
    embedder: Embedder = Depends(get_embedder),
) -> MemoryOut:
    updated = memory_service.update_memory(connection, memory_id, payload.content)
    if updated.approved:
        retrieval_service.store_embedding(connection, memory_id, embedder)
    return updated


@router.post("/{memory_id}/approve", response_model=MemoryOut)
def approve_memory(
    memory_id: int,
    connection: sqlite3.Connection = Depends(get_connection),
    embedder: Embedder = Depends(get_embedder),
) -> MemoryOut:
    approved = memory_service.approve_memory(connection, memory_id)
    retrieval_service.store_embedding(connection, memory_id, embedder)
    return approved


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(
    memory_id: int,
    connection: sqlite3.Connection = Depends(get_connection),
) -> Response:
    memory_service.delete_memory(connection, memory_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
