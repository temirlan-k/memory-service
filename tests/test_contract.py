import pytest
import httpx

USER_ID = "test-contract-user"
SESSION_ID = "test-contract-session"

TURN = {
    "session_id": SESSION_ID,
    "user_id": USER_ID,
    "messages": [
        {"role": "user", "content": "I work at Notion and live in Berlin."},
        {"role": "assistant", "content": "Nice! How do you like Berlin?"},
    ],
    "timestamp": "2025-03-15T10:00:00Z",
    "metadata": {},
}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_turns_returns_201_with_id(client):
    r = client.post("/turns", json=TURN)
    assert r.status_code == 201
    body = r.json()
    assert "id" in body
    assert isinstance(body["id"], str)


def test_memories_available_after_turn(client):
    client.post("/turns", json=TURN)
    r = client.get(f"/users/{USER_ID}/memories")
    assert r.status_code == 200
    body = r.json()
    assert "memories" in body
    assert isinstance(body["memories"], list)
    assert len(body["memories"]) > 0


def test_memory_schema(client):
    client.post("/turns", json=TURN)
    memories = client.get(f"/users/{USER_ID}/memories").json()["memories"]
    m = memories[0]
    for field in ("id", "type", "key", "value", "confidence", "source_session", "source_turn", "active", "created_at", "updated_at"):
        assert field in m, f"missing field: {field}"


def test_recall_returns_200(client):
    client.post("/turns", json=TURN)
    r = client.post("/recall", json={
        "query": "Where does the user work?",
        "session_id": SESSION_ID,
        "user_id": USER_ID,
        "max_tokens": 512,
    })
    assert r.status_code == 200
    body = r.json()
    assert "context" in body
    assert "citations" in body


def test_recall_cold_session_returns_empty(client):
    r = client.post("/recall", json={
        "query": "Where does the user live?",
        "session_id": "nonexistent",
        "user_id": "nonexistent-user",
        "max_tokens": 512,
    })
    assert r.status_code == 200
    assert r.json() == {"context": "", "citations": []}


def test_delete_session(client):
    client.post("/turns", json=TURN)
    r = client.delete(f"/sessions/{SESSION_ID}")
    assert r.status_code == 204
    memories = client.get(f"/users/{USER_ID}/memories").json()["memories"]
    assert len(memories) == 0


def test_delete_user(client):
    client.post("/turns", json=TURN)
    r = client.delete(f"/users/{USER_ID}")
    assert r.status_code == 204
    memories = client.get(f"/users/{USER_ID}/memories").json()["memories"]
    assert len(memories) == 0


def test_search_returns_results(client):
    client.post("/turns", json=TURN)
    r = client.post("/search", json={
        "query": "Notion",
        "user_id": USER_ID,
        "limit": 5,
    })
    assert r.status_code == 200
    body = r.json()
    assert "results" in body
    assert isinstance(body["results"], list)
