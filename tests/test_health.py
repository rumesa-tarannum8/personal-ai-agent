from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_health_returns_ok(tmp_path: Path) -> None:
    settings = Settings(database_path=tmp_path / "test.db")
    client = TestClient(create_app(settings))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_startup_creates_sqlite_file(tmp_path: Path) -> None:
    db_path = tmp_path / "agent.db"
    settings = Settings(database_path=db_path)
    with TestClient(create_app(settings)):
        assert db_path.exists()
        assert db_path.stat().st_size > 0
