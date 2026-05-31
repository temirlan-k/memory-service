# Memory Service

A memory service for AI agents - ingests conversation turns, extracts structured facts, and answers recall queries.

## Architecture

```
POST /turns
    │
    ├── Pass 1: Observation extraction (LLM)
    │       "User walked Biscuit" → raw observations
    │
    ├── Pass 2: Entity extraction (LLM)
    │       observations → typed entities (LOCATION, ORGANIZATION, ANIMAL, ...)
    │
    ├── Deterministic key mapping (Python)
    │       LOCATION/current_city → location.current_city
    │
    ├── Embedding (text-embedding-3-small)
    │
    ├── Key normalization (LLM) — maps drift keys to existing canonical keys
    │       "employment.current_employer" → "employment.current_company"
    │
    └── Save to PostgreSQL (atomic with turn via UoW)
            └── Supersession: if key exists → mark old active=false

POST /recall
    │
    ├── Query expansion (LLM) → 2-3 keyword phrases
    ├── BM25 (PostgreSQL tsvector) × all queries
    ├── Vector search (pgvector cosine)
    ├── RRF fusion
    ├── Stable facts (personal/employment/location — always included first)
    ├── Context assembly under token budget
    └── LLM formatting → readable sentences
```

FastAPI + PostgreSQL + pgvector. Single container + postgres, no separate vector store.

## Backing store

PostgreSQL with pgvector Opted for it over dedicated vector store (Qdrant, Milvus) One less service to run One less point of failure At this scale, pgvector takes care of the vector similarity. BM25 using native `tsvector`/`tsquery` – no additional infrastructure.
## Extraction pipeline

Two-pass per turn:

**Pass 1: observations.** LLM lists raw facts without schema: "User works at Notion", "User walked an entity named Biscuit". No key mapping yet.

**Pass 2: entity extraction.** LLM returns typed entities: `{value: "Biscuit", category: "ANIMAL", attribute: "pet_name", confidence: 0.85}`. Categories are constrained to 8 types (LOCATION, ORGANIZATION, ANIMAL, PERSON, PREFERENCE, OPINION, GOAL, ATTRIBUTE).

**Deterministic key mapping.** Python maps category → prefix: `ANIMAL → personal`, `LOCATION → location`. Final key: `personal.pet_name`. LLM never picks the canonical key — this prevents cities from landing in `employment.*`.

**Key normalization.** Before saving, each new key is compared against the user's existing keys. If LLM extracted `employment.current_employer` but `employment.current_company` already exists, they're matched as the same concept and supersession fires correctly. Falls back to new key if no match.

Models: `gpt-4o-mini` via OpenRouter for extraction, `text-embedding-3-small` for embeddings.

## Recall strategy

1. **Query expansion** — LLM rewrites query into 2-3 keyword phrases. Improves BM25 on vague queries.
2. **Hybrid search** — BM25 + vector, fused with RRF (k=60). BM25 catches token matches, vector catches semantics.
3. **Token budget priority:** stable facts first (`personal.*`, `employment.*`, `location.*`), then query-relevant by RRF. Minimum threshold 0.02 — below this, memory is excluded to avoid noise.

Context is LLM-formatted into readable sentences. Falls back to raw `key: value` on failure.

## Fact evolution

Supersession on insert: `WHERE user_id=? AND key=? AND active=true` → mark old `active=false`, link via `supersedes_id`. History preserved, never deleted.

`/recall` surfaces only `active=true`. `GET /users/{id}/memories` returns full chain.

**Known limitations:**
- Free-form `attribute` can vary between runs (`goal.interview_preparation` vs `goal.upcoming_interview`) — treated as different keys, no supersession. Requires fixed attribute vocabulary or a normalization pass to fix.
- 8 category types don't cover all domains — education maps to `employment.*`, health conditions land in `opinion.*`. For uncommon categories, supersession degrades but vector recall still surfaces relevant memories semantically. The tradeoff: open schema means universal coverage, closed schema means reliable supersession. This system chooses coverage.

## Cross-session scoping

Memories are scoped to `user_id`, not `session_id`. All sessions for the same user share one memory store — intentional, user facts are stable across conversations.

## Tradeoffs

- 2 LLM calls per extraction + 2 per recall. Latency ~2-4s per operation. Acceptable given 60s timeout.
- Synchronous extraction — turn not saved if LLM fails. Async queue would give resilience but violates the spec requirement that memories are queryable immediately after POST /turns returns.
- Exact key supersession — fast, breaks on key drift. Key normalizer reduces drift but adds one LLM call per turn. Vector-based supersession would eliminate drift entirely but requires embedding comparison on every insert.

## Failure modes

- **Missing API keys** — extraction returns empty, turn not saved (UoW rollback). `/recall` returns empty context.
- **LLM failure** — query expansion falls back to original query. Context formatting falls back to raw key:value.
- **Unknown user** — `/recall` returns `{"context": "", "citations": []}`, no error.
- **DB unavailable** — 500, UoW rolls back, no partial state.
- **Prompt injection** — messages containing injection patterns ("ignore previous instructions", "forget everything") are filtered before extraction. Limitation: entire message is dropped, not just the injection part — legitimate facts in the same message are lost.

## How to run

```bash
git clone <repo> memory-service
cd memory-service
cp .env.example .env  # set AI__LLM_API_KEY
docker compose up -d
until curl -sf http://localhost:8080/health; do sleep 1; done
```

## How to run tests

```bash
docker compose up -d
until curl -sf http://localhost:8080/health; do sleep 1; done

# Contract + robustness + session isolation
pip install httpx pytest
pytest tests/ -v --ignore=tests/test_recall_quality.py

# Recall quality fixture (~60s, makes LLM calls)
pytest tests/test_recall_quality.py -v -s
```
