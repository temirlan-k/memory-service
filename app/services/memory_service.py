from __future__ import annotations

import structlog

from app.api.schemas import TurnRequest
from app.infra.db.models.turn import Turn
from app.infra.db.unit_of_work import UnitOfWork

log = structlog.get_logger()


class MemoryService:

    async def ingest_turn(self, uow: UnitOfWork, data: TurnRequest) -> Turn:
        try:
            turn = await uow.turns.create(data)
            log.info("turn_saved", service=self.__class__.__name__, turn_id=str(turn.id), session_id=data.session_id)
            return turn
        except Exception as e:
            log.error("ingest_turn_failed", session_id=data.session_id, error=str(e))
            raise
