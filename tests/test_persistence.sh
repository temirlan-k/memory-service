#!/bin/bash
set -e

BASE_URL="${SERVICE_URL:-http://localhost:8080}"

echo "=== Persistence test ==="

# 1. Write data
echo "Writing turn..."
curl -sf -X POST "$BASE_URL/turns" \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id": "persist-test",
    "user_id": "persist-user",
    "messages": [
      {"role": "user", "content": "I live in Tokyo and work at Sony."},
      {"role": "assistant", "content": "Nice!"}
    ],
    "timestamp": "2025-01-01T00:00:00Z",
    "metadata": {}
  }' > /dev/null

# 2. Verify data exists
COUNT=$(curl -sf "$BASE_URL/users/persist-user/memories" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['memories']))")
echo "Memories before restart: $COUNT"
[ "$COUNT" -gt 0 ] || { echo "FAIL: no memories before restart"; exit 1; }

# 3. Restart
echo "Restarting service..."
docker compose restart app
sleep 5
until curl -sf "$BASE_URL/health" > /dev/null; do sleep 1; done

# 4. Verify data survives
COUNT_AFTER=$(curl -sf "$BASE_URL/users/persist-user/memories" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['memories']))")
echo "Memories after restart: $COUNT_AFTER"
[ "$COUNT_AFTER" -gt 0 ] || { echo "FAIL: data lost after restart"; exit 1; }

# 5. Cleanup
curl -sf -X DELETE "$BASE_URL/users/persist-user" > /dev/null

echo "PASS: data survived restart ($COUNT_AFTER memories)"
