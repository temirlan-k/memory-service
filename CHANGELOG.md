# Dev Log

## v1: Bootstrapping

FastAPI, PostgreSQL, Docker. pgvector over Qdrant/Milvus — one less service. uv over pip — faster, cleaner lockfiles in Docker.

---

## v2: Data model

Raw message chunks make fact evolution impossible — can't tell `"works at Stripe"` and `"joined Notion"` are the same fact. Switched to key/value.

- `confidence` — hedged statements (`"might move to Berlin"`) get lower weight in recall
- `active` + `supersedes_id` — soft delete, history preserved, `/recall` filters `active=true`

---

## v3: Infrastructure fixes

Turn saved but extraction failed — turn in DB with no memories. Unit of Work: turn + memories commit together, rollback on failure.

`postgres:17-alpine` — pgvector missing. Switched to `pgvector/pgvector:pg17`.

Settings re-read `.env` on every import. Moved to singletons.

---

## v4: Extraction pipeline

`response_format={"type": "json_object"}` — OpenRouter ignored it. Switched to tool calling via `instructor` — schema enforced at API level.

Supersession via exact key match (`WHERE key=? AND active=true`). Simple, fast. Tradeoff: breaks on key drift.

---

## v5: Two-pass extraction

Single-pass missed implicit facts — model doing too many things at once. Split: Pass 1 lists raw observations, Pass 2 infers structured facts. Each pass has one job.

Result: `pet_name`, `previous_city`, opinions extracted consistently.

---

## v6: Entity-based extraction with deterministic key mapping

Pass 2 picked canonical keys directly — `"NYC"` landed in `employment.previous_company` because model guessed from context, not entity type.

Changed to typed entities (LOCATION, ORGANIZATION, ANIMAL, ...) + free-form attribute. Python mapper converts category → key prefix. LLM classifies, code builds the key.

Remaining: free-form attribute varies between runs — not a bug, known non-determinism.

---

## v7: /recall — hybrid search + query rewriting

Cosine top-k missed keyword queries. Added BM25 (tsvector) + vector, fused with RRF. Query rewriting expands into 2-3 phrases before BM25.

Minimum RRF threshold (0.02) — filters noise on unrelated queries, "Relevant" section stays empty instead of returning everything.

Raw key=value unreadable for LLM agent. Added formatting pass — `"personal.pet_name=Biscuit"` → `"Has a pet named Biscuit"`. Falls back to raw on failure.

---

## v8: /search, tests, hardening

POST /search — same HybridSearcher, no LLM calls. Agent tool — latency over quality.

Tests: contract roundtrip, session isolation, malformed input, recall quality fixture.

- `supersedes_id` FK blocked DELETE /users. Added `ondelete="SET NULL"`
- Token budget on raw values, LLM outputs ~4x longer. Added overhead multiplier
- BM25 ran twice per query. Cached first pass
- QueryExpander had no examples. Added few-shot with keyword phrases

---

## v9: Key normalization + prompt injection

Supersession broke on key drift — `employment.current_employer` vs `employment.current_company`, both active after job change.

KeyNormalizer: before saving, LLM checks if new key matches existing key with same prefix. Match → use existing key, supersession fires. +1 LLM call/turn.

Prompt injection: regex filter drops messages with injection patterns before extraction. Tradeoff: real facts in the same message are lost too.
---

## v10: is_stable field + DI fix

`get_stable_facts` used prefix matching (`personal.*`, `employment.*`, ...) — adding a new category meant updating two separate lists in different files. Missed one → facts silently missing from context.

Replaced with `is_stable` boolean field on Memory. Set at extraction time based on category — OPINION and GOAL are unstable, everything else is stable. Single source of truth in `_UNSTABLE_CATEGORIES`. `get_stable_facts` now queries `WHERE is_stable=True`.

UoW opened a DB session before request body validation — 422 errors triggered unnecessary DB transactions. Changed DI to return UoW object without opening session. Services call `async with uow:` themselves — session opens only when actually needed.
