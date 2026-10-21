from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.db import connect, init_db
from app.routes.health import router as health_router
from app.routes.memories import router as memories_router
from app.services.embeddings import Embedder


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    connection = connect(settings.database_path)
    init_db(connection)
    app.state.db = connection
    try:
        yield
    finally:
        connection.close()


def create_app(
    settings: Optional[Settings] = None,
    embedder: Optional[Embedder] = None,
) -> FastAPI:
    app = FastAPI(
        title="Personal AI Agent",
        description="Context-aware personal agent with explicit long-term memory.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = settings or get_settings()
    app.state.embedder = embedder
    app.include_router(health_router)
    app.include_router(memories_router)
    return app


app = create_app()
