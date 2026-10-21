from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.embeddings import cosine_similarity
from tests.fakes import FakeEmbedder


def test_cosine_similarity_identical_and_orthogonal() -> None:
    identical = cosine_similarity(
        np.array([1.0, 0.0]),
        np.array([[1.0, 0.0]]),
    )
    orthogonal = cosine_similarity(
        np.array([1.0, 0.0]),
        np.array([[0.0, 1.0]]),
    )

    assert identical[0] == pytest.approx(1.0)
    assert orthogonal[0] == pytest.approx(0.0)


def test_retrieve_ranks_relevant_approved_memory(client: TestClient) -> None:
    peanuts = client.post(
        "/memories", json={"content": "I am allergic to peanuts"}
    ).json()
    color = client.post(
        "/memories", json={"content": "My favorite color is blue"}
    ).json()
    client.post(f"/memories/{peanuts['id']}/approve")
    client.post(f"/memories/{color['id']}/approve")

    response = client.get(
        "/memories/retrieve",
        params={"q": "What food should I avoid because of an allergy?"},
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == [peanuts["id"], color["id"]]
    assert items[0]["score"] > items[1]["score"]
    assert items[0]["content"] == "I am allergic to peanuts"


def test_retrieve_ignores_unapproved_memories(client: TestClient) -> None:
    pending = client.post(
        "/memories", json={"content": "I am allergic to peanuts"}
    ).json()
    approved = client.post(
        "/memories", json={"content": "Morning meetings are preferred"}
    ).json()
    client.post(f"/memories/{approved['id']}/approve")

    response = client.get(
        "/memories/retrieve",
        params={"q": "food allergy peanuts to avoid"},
    )

    ids = [item["id"] for item in response.json()["items"]]
    assert pending["id"] not in ids
    assert ids == [approved["id"]]


def test_retrieve_uses_stored_embeddings_after_restart(db_path: Path) -> None:
    settings = Settings(database_path=db_path)
    embedder = FakeEmbedder()

    with TestClient(create_app(settings, embedder=embedder)) as first:
        created = first.post(
            "/memories", json={"content": "I am allergic to peanuts"}
        ).json()
        first.post(f"/memories/{created['id']}/approve")
        memory_id = created["id"]

    with TestClient(create_app(settings, embedder=embedder)) as second:
        response = second.get(
            "/memories/retrieve",
            params={"q": "food I should avoid because of peanut allergy"},
        )
        items = response.json()["items"]
        assert items[0]["id"] == memory_id
        assert items[0]["score"] > 0
