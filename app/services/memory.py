import sqlite3
from typing import List, Optional

from fastapi import HTTPException, status

from app.schemas import MemoryOut


def _row_to_memory(row: sqlite3.Row) -> MemoryOut:
    return MemoryOut(
        id=row["id"],
        content=row["content"],
        approved=bool(row["approved"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_memory(connection: sqlite3.Connection, content: str) -> MemoryOut:
    cursor = connection.execute(
        """
        INSERT INTO memories (content, approved)
        VALUES (?, 0)
        """,
        (content,),
    )
    connection.commit()
    return get_memory(connection, cursor.lastrowid)


def get_memory(connection: sqlite3.Connection, memory_id: int) -> MemoryOut:
    row = connection.execute(
        "SELECT id, content, approved, created_at, updated_at FROM memories WHERE id = ?",
        (memory_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory {memory_id} not found",
        )
    return _row_to_memory(row)


def list_memories(
    connection: sqlite3.Connection,
    approved: Optional[bool] = None,
) -> List[MemoryOut]:
    sql = "SELECT id, content, approved, created_at, updated_at FROM memories"
    params: tuple = ()
    if approved is not None:
        sql += " WHERE approved = ?"
        params = (1 if approved else 0,)
    sql += " ORDER BY id ASC"
    rows = connection.execute(sql, params).fetchall()
    return [_row_to_memory(row) for row in rows]


def search_memories(
    connection: sqlite3.Connection,
    query: str,
    approved: Optional[bool] = None,
) -> List[MemoryOut]:
    pattern = f"%{query.strip()}%"
    sql = """
        SELECT id, content, approved, created_at, updated_at
        FROM memories
        WHERE content LIKE ? COLLATE NOCASE
    """
    params: List[object] = [pattern]
    if approved is not None:
        sql += " AND approved = ?"
        params.append(1 if approved else 0)
    sql += " ORDER BY id ASC"
    rows = connection.execute(sql, params).fetchall()
    return [_row_to_memory(row) for row in rows]


def update_memory(
    connection: sqlite3.Connection, memory_id: int, content: str
) -> MemoryOut:
    get_memory(connection, memory_id)
    connection.execute(
        """
        UPDATE memories
        SET content = ?, updated_at = CURRENT_TIMESTAMP, embedding = NULL
        WHERE id = ?
        """,
        (content, memory_id),
    )
    connection.commit()
    return get_memory(connection, memory_id)


def approve_memory(connection: sqlite3.Connection, memory_id: int) -> MemoryOut:
    get_memory(connection, memory_id)
    connection.execute(
        """
        UPDATE memories
        SET approved = 1, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (memory_id,),
    )
    connection.commit()
    return get_memory(connection, memory_id)


def delete_memory(connection: sqlite3.Connection, memory_id: int) -> None:
    get_memory(connection, memory_id)
    connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    connection.commit()
