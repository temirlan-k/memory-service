import pytest


def test_missing_session_id(client):
    r = client.post("/turns", json={
        "user_id": "user-1",
        "messages": [{"role": "user", "content": "hello"}],
        "timestamp": "2025-01-01T00:00:00Z",
        "metadata": {},
    })
    assert r.status_code == 422


def test_missing_messages(client):
    r = client.post("/turns", json={
        "session_id": "s1",
        "user_id": "user-1",
        "timestamp": "2025-01-01T00:00:00Z",
        "metadata": {},
    })
    assert r.status_code == 422


def test_invalid_message_role(client):
    r = client.post("/turns", json={
        "session_id": "s1",
        "user_id": "user-1",
        "messages": [{"role": "invalid_role", "content": "hello"}],
        "timestamp": "2025-01-01T00:00:00Z",
        "metadata": {},
    })
    assert r.status_code == 422


def test_invalid_json(client):
    r = client.post("/turns", content=b"not json", headers={"Content-Type": "application/json"})
    assert r.status_code == 422


def test_unicode_content(client):
    r = client.post("/turns", json={
        "session_id": "unicode-session",
        "user_id": "unicode-user",
        "messages": [
            {"role": "user", "content": "Привет! 你好 🎉 مرحبا"},
            {"role": "assistant", "content": "Hello back!"},
        ],
        "timestamp": "2025-01-01T00:00:00Z",
        "metadata": {},
    })
    assert r.status_code == 201


def test_recall_no_user_id(client):
    r = client.post("/recall", json={
        "query": "anything",
        "session_id": "s1",
        "user_id": None,
        "max_tokens": 512,
    })
    assert r.status_code == 200
    assert r.json() == {"context": "", "citations": []}


def test_empty_messages_list(client):
    r = client.post("/turns", json={
        "session_id": "s1",
        "user_id": "user-1",
        "messages": [],
        "timestamp": "2025-01-01T00:00:00Z",
        "metadata": {},
    })
    assert r.status_code in (201, 422)
