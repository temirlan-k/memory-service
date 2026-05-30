## v1: Bootstrapping

Basic project setup: FastAPI, PostgreSQL, Docker. Chose pgvector vs a separate vector store like qdrant/milvus to keep it simple, one less service to maintain.
Used uv instead of pip, since it's faster and handles lockfiles in Docker nicely.
Container up and running, health check is working, Alembic migrations and structlog configured.
---

## v2: Data model

Could store text chunks from turns directly into Memory, but fact evolution would be impossible — no way to tell "works at Stripe" and "just joined Notion" are the same fact. Switched to key/value so contradictions are detectable by key.

Some field notes worth mentioning:
- confidence: LLM is not always sure, "might move to Berlin" vs "lives in Berlin" are different weights for recall ranking
- embedding: nullable, can save memory first and then embed separately, no blocking of main flow
- active + supersedes_id: soft delete, old fact stays in history and new references it. In the future /recall filters active=true /users/{id}/memories shows the full chain
---

## v3: Infrastructure fixes

Turn and Memories to make a joint commitment. Needed If extraction fails , the turn should not be saved either .
Changed to Unit of Work for that atomicity: repo gets session in constructor, UoW owns commit/rollback.
UoW fixed that as a side effect. Passing session through every method was also getting messy.

Initially used postgres:17-alpine, had an issue, the pgvector extension was not installed.
Change to pgvector/pgvector:pg17, fix obvious.

Settings were instantiated multiple times in the code base, and every time it re-read .env.
Moved to singletons in config/__init__.py

Service boots, migrations on startup, POST /turns saves. Next extraction.
