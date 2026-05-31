import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fixtures.conversations import CONVERSATIONS, PROBES

USER_ID = "fixture-user"


def setup_fixture(client):
    client.delete(f"/users/{USER_ID}")
    for conv in CONVERSATIONS:
        r = client.post("/turns", json={**conv, "metadata": {}})
        assert r.status_code == 201, f"Failed to ingest turn: {r.text}"


def test_recall_quality(client):
    setup_fixture(client)

    passed = 0
    total = len(PROBES)

    for probe in PROBES:
        r = client.post("/recall", json={
            "query": probe["query"],
            "session_id": "fixture-session",
            "user_id": USER_ID,
            "max_tokens": 1024,
        })
        assert r.status_code == 200
        context = r.json()["context"].lower()

        hit = all(exp.lower() in context for exp in probe["expected_in_context"])
        no_bleed = all(bad.lower() not in context for bad in probe["not_expected"])

        if hit and no_bleed:
            passed += 1
        else:
            missed = [e for e in probe["expected_in_context"] if e.lower() not in context]
            bled = [b for b in probe["not_expected"] if b.lower() in context]
            print(f"\nFAIL: '{probe['query']}'")
            if missed:
                print(f"  Missing: {missed}")
            if bled:
                print(f"  Unexpected: {bled}")

    print(f"\nRecall quality: {passed}/{total}")
    assert passed >= total * 0.8, f"Recall quality too low: {passed}/{total}"
