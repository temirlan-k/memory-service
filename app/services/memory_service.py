from __future__ import annotations

import structlog

from app.api.schemas import TurnRequest
from app.infra.db.models import Memory
from app.infra.db.models.turn import Turn
from app.infra.db.unit_of_work import UnitOfWork
from app.services.extraction_service import ExtractionService
from app.services.embedding_service import EmbeddingService
from app.services.key_normalizer import KeyNormalizer
from app.services.sanitizer import sanitize_messages

log = structlog.get_logger()


class MemoryService:

    def __init__(self, extraction_service: ExtractionService, embedding_service: EmbeddingService, key_normalizer: KeyNormalizer) -> None:
        self._extraction = extraction_service
        self._embedding = embedding_service
        self._normalizer = key_normalizer

    async def ingest_turn(self, uow: UnitOfWork, data: TurnRequest) -> Turn:
        try:
            turn = await uow.turns.create(data)
            memories = await self._extract_memories(uow, data)
            if memories:
                await self._embed_and_save(uow, memories, turn, data.user_id)
            log.info("turn_saved", turn_id=str(turn.id), session_id=data.session_id)
            return turn
        except Exception as e:
            log.error("ingest_turn_failed", session_id=data.session_id, error=str(e))
            raise

    async def _extract_memories(self, uow: UnitOfWork, data: TurnRequest) -> list[dict]:
        messages = sanitize_messages([m.model_dump() for m in data.messages])
        extracted = await self._extraction.extract_memories(messages)
        if not extracted or not data.user_id:
            return extracted
        existing_keys = [m.key for m in await uow.memories.get_by_user(data.user_id)]
        return await self._normalizer.normalize_all(extracted, existing_keys)

    async def _embed_and_save(self, uow: UnitOfWork, memories: list[dict], turn: Turn, user_id: str | None) -> None:
        texts = [f"{m['key']} {m['value']}" for m in memories]
        embeddings = await self._embedding.embed_texts(texts)
        for i, m in enumerate(memories):
            m["embedding"] = embeddings[i]
        await uow.memories.save_all(memories, turn, user_id)

    async def get_user_memories(self, uow: UnitOfWork, user_id: str) -> list[Memory]:
        return await uow.memories.get_by_user(user_id)

    async def delete_session(self, uow: UnitOfWork, session_id: str) -> None:
        await uow.turns.delete_by_session(session_id)

    async def delete_user(self, uow: UnitOfWork, user_id: str) -> None:
        await uow.turns.delete_by_user(user_id)
