import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models.memory import Memory
from app.infra.db.models.turn import Turn

log = structlog.get_logger()


class MemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_all(
        self,
        extracted: list[dict],
        turn: Turn,
        user_id: str | None,
    ) -> None:
        try:
            for item in extracted:
                supersedes_id = await self._supersede_existing(user_id, item["key"])
                memory = Memory(
                    user_id=user_id,
                    source_session_id=turn.session_id,
                    source_turn_id=turn.id,
                    type=item["type"],
                    key=item["key"],
                    value=item["value"],
                    confidence=item.get("confidence", 1.0),
                    embedding=item.get("embedding") or None,
                    supersedes_id=supersedes_id,
                )
                self.session.add(memory)
            await self.session.flush()
            log.info("memories_saved", count=len(extracted), turn_id=str(turn.id))
        except SQLAlchemyError as e:
            log.error("memories_save_failed", turn_id=str(turn.id), error=str(e))
            raise

    async def _supersede_existing(self, user_id: str | None, key: str) -> uuid.UUID | None:
        if not user_id:
            return None

        result = await self.session.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.key == key,
                Memory.active == True
            )
        )

        existing = result.scalar_one_or_none()
        if existing is None:
            return None

        existing.active = False
        return existing.id

    async def get_by_user(self, user_id: str) -> list[Memory]:
        result = await self.session.execute(
            select(Memory).where(Memory.user_id == user_id).order_by(Memory.created_at.desc())
        )
        return list(result.scalars().all())
