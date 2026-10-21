from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.fakes import FakeEmbedder


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "agent.db"


@pytest.fixture
def client(db_path: Path) -> TestClient:
    settings = Settings(database_path=db_path)
    with TestClient(create_app(settings, embedder=FakeEmbedder())) as test_client:
        yield test_client
