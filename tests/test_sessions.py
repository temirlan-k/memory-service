USER_A = "test-session-user-a"
USER_B = "test-session-user-b"


def test_sessions_dont_bleed(client):
    client.post("/turns", json={
        "session_id": "session-a",
        "user_id": USER_A,
        "messages": [
            {"role": "user", "content": "I work at Apple and live in San Francisco."},
            {"role": "assistant", "content": "Nice!"},
        ],
        "timestamp": "2025-01-01T00:00:00Z",
        "metadata": {},
    })

    client.post("/turns", json={
        "session_id": "session-b",
        "user_id": USER_B,
        "messages": [
            {"role": "user", "content": "I work at Google and live in New York."},
            {"role": "assistant", "content": "Great!"},
        ],
        "timestamp": "2025-01-01T00:00:00Z",
        "metadata": {},
    })

    memories_a = client.get(f"/users/{USER_A}/memories").json()["memories"]
    memories_b = client.get(f"/users/{USER_B}/memories").json()["memories"]

    values_a = {m["value"] for m in memories_a}
    values_b = {m["value"] for m in memories_b}

    assert "Google" not in values_a
    assert "New York" not in values_a
    assert "Apple" not in values_b
    assert "San Francisco" not in values_b
