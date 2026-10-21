# Personal AI Agent

A FastAPI service that chats with an LLM and stores **explicitly approved** long-term memories in SQLite. Memories persist across restarts and are retrieved with sentence embeddings and cosine similarity.

## Status

Milestones 1–3 are implemented and covered by tests: app factory, SQLite, memory CRUD with explicit approval, and cosine retrieval over approved memories. LLM chat is not implemented yet.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

API keys belong in `.env`, never in source files.

## Run

```bash
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/health`.

### Memory API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/memories` | Create a memory (always unapproved) |
| `GET` | `/memories` | List memories (`?approved=true\|false`) |
| `GET` | `/memories/search?q=` | Case-insensitive substring search |
| `GET` | `/memories/retrieve?q=` | Semantic search of **approved** memories |
| `GET` | `/memories/{id}` | Fetch one memory |
| `PATCH` | `/memories/{id}` | Update content (re-embeds if already approved) |
| `POST` | `/memories/{id}/approve` | Approve and store an embedding |
| `DELETE` | `/memories/{id}` | Delete |

New memories are **not** approved until `POST /memories/{id}/approve`. Retrieval never includes pending memories.

`GET /memories/retrieve` embeds the query, loads stored embeddings from SQLite, and ranks by cosine similarity. Optional query params: `limit` (1–50, default 5) and `min_score` (−1 to 1, default 0).

## Tests

```bash
pytest
```

## Architecture

- **FastAPI** serves REST endpoints.
- **SQLite** stores conversations, messages, and memories on disk.
- **Settings** load from environment variables (`DATABASE_PATH`, `LLM_API_KEY`, …).
- **MemoryService** writes to SQLite. Approval is a separate step from create/update.
- **SentenceTransformerEmbedder** (`all-MiniLM-L6-v2` by default) turns text into vectors. Tests inject a tiny fake embedder so CI does not download the model.
- **RetrievalService** stores embeddings as BLOBs and ranks only `approved = 1` rows with cosine similarity.
- Later milestone: LLM chat that uses retrieved memories.
