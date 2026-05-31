from __future__ import annotations

import structlog

from app.api.schemas import TurnRequest
from app.infra.db.models.turn import Turn
from app.infra.db.unit_of_work import UnitOfWork
from app.services.extraction_service import ExtractionService
from app.services.embedding_service import EmbeddingService

log = structlog.get_logger()


class MemoryService:

    def __init__(self, extraction_service: ExtractionService, embedding_service: EmbeddingService) -> None:
        self._extraction = extraction_service
        self._embedding = embedding_service

    async def ingest_turn(self, uow: UnitOfWork, data: TurnRequest) -> Turn:
        try:
            turn = await uow.turns.create(data)
            messages = [m.model_dump() for m in data.messages]
            extracted = await self._extraction.extract_memories(messages)

            if extracted:
                texts = [f"{m['key']} {m['value']}" for m in extracted]
                embeddings = await self._embedding.embed_texts(texts)
                for i, m in enumerate(extracted):
                    m["embedding"] = embeddings[i]
                await uow.memories.save_all(extracted, turn, data.user_id)
            log.info("turn_saved", service=self.__class__.__name__, turn_id=str(turn.id), session_id=data.session_id)
            return turn
        except Exception as e:
            log.error("ingest_turn_failed", session_id=data.session_id, error=str(e))
            raise
