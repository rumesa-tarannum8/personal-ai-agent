from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.fakes import FakeEmbedder


def test_create_memory_defaults_to_unapproved(client: TestClient) -> None:
    response = client.post("/memories", json={"content": "I drink oat milk."})

    assert response.status_code == 201
    body = response.json()
    assert body["content"] == "I drink oat milk."
    assert body["approved"] is False
    assert body["id"] >= 1


def test_create_memory_rejects_blank_content(client: TestClient) -> None:
    response = client.post("/memories", json={"content": "   "})

    assert response.status_code == 422


def test_list_and_approve_memory(client: TestClient) -> None:
    created = client.post("/memories", json={"content": "Lives in Boston"}).json()

    pending = client.get("/memories", params={"approved": False})
    assert pending.status_code == 200
    assert [item["id"] for item in pending.json()["items"]] == [created["id"]]

    approved_list = client.get("/memories", params={"approved": True})
    assert approved_list.json()["items"] == []

    approve = client.post(f"/memories/{created['id']}/approve")
    assert approve.status_code == 200
    assert approve.json()["approved"] is True

    approved_list = client.get("/memories", params={"approved": True})
    assert [item["id"] for item in approved_list.json()["items"]] == [created["id"]]


def test_search_memories_is_case_insensitive(client: TestClient) -> None:
    client.post("/memories", json={"content": "Favorite color is teal"})
    client.post("/memories", json={"content": "Allergic to peanuts"})

    response = client.get("/memories/search", params={"q": "TEAL"})

    assert response.status_code == 200
    contents = [item["content"] for item in response.json()["items"]]
    assert contents == ["Favorite color is teal"]


def test_update_memory_content(client: TestClient) -> None:
    created = client.post("/memories", json={"content": "Has a cat"}).json()

    response = client.patch(
        f"/memories/{created['id']}", json={"content": "Has two cats"}
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Has two cats"
    fetched = client.get(f"/memories/{created['id']}")
    assert fetched.json()["content"] == "Has two cats"


def test_delete_memory(client: TestClient) -> None:
    created = client.post("/memories", json={"content": "Temporary note"}).json()

    response = client.delete(f"/memories/{created['id']}")

    assert response.status_code == 204
    missing = client.get(f"/memories/{created['id']}")
    assert missing.status_code == 404
    assert missing.json()["detail"] == f"Memory {created['id']} not found"


def test_missing_memory_returns_404(client: TestClient) -> None:
    assert client.get("/memories/999").status_code == 404
    assert client.post("/memories/999/approve").status_code == 404
    assert client.patch("/memories/999", json={"content": "x"}).status_code == 404
    assert client.delete("/memories/999").status_code == 404


def test_memories_persist_after_app_restart(db_path: Path) -> None:
    settings = Settings(database_path=db_path)

    with TestClient(create_app(settings, embedder=FakeEmbedder())) as first:
        created = first.post(
            "/memories", json={"content": "Prefers morning meetings"}
        ).json()
        first.post(f"/memories/{created['id']}/approve")
        memory_id = created["id"]

    with TestClient(create_app(settings, embedder=FakeEmbedder())) as second:
        response = second.get(f"/memories/{memory_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["content"] == "Prefers morning meetings"
        assert body["approved"] is True
