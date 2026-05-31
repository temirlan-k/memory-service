import uuid

import structlog
from sqlalchemy import select, func, text
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
                    is_stable=item.get("is_stable", True),
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

        existing_all = list(result.scalars().all())
        if not existing_all:
            return None

        latest = max(existing_all, key=lambda m: m.created_at)
        for m in existing_all:
            m.active = False
        return latest.id

    async def get_by_user(self, user_id: str) -> list[Memory]:
        result = await self.session.execute(
            select(Memory).where(Memory.user_id == user_id).order_by(Memory.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_stable_facts(self, user_id: str) -> list[Memory]:
        result = await self.session.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.active == True,  # noqa: E712
                Memory.is_stable == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def search_bm25(self, user_id: str, query: str, limit: int = 20) -> list[Memory]:
        search_text = func.to_tsvector("english", Memory.key + " " + Memory.value)
        search_query = func.plainto_tsquery("english", query)
        result = await self.session.execute(
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.active == True,  # noqa: E712
                search_text.op("@@")(search_query),
            )
            .order_by(func.ts_rank(search_text, search_query).desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_vector(self, user_id: str, embedding: list[float], limit: int = 20) -> list[tuple[Memory, float]]:
        distance = Memory.embedding.cosine_distance(embedding).label("distance")
        result = await self.session.execute(
            select(Memory, distance)
            .where(
                Memory.user_id == user_id,
                Memory.active == True,  # noqa: E712
                Memory.embedding.is_not(None),
            )
            .order_by(text("distance"))
            .limit(limit)
        )
        return [(row.Memory, row.distance) for row in result.all()]
