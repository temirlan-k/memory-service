import structlog
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models.session import Session
from app.infra.db.models.turn import Turn
from app.api.schemas.turn import TurnRequest

log = structlog.get_logger()


class TurnRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_or_create_session(self, session_id: str, user_id: str | None) -> Session:
        result = await self.session.execute(select(Session).where(Session.id == session_id))
        db_session = result.scalar_one_or_none()
        if db_session is None:
            db_session = Session(id=session_id, user_id=user_id)
            self.session.add(db_session)
            await self.session.flush()
        return db_session

    async def create(self, data: TurnRequest) -> Turn:
        try:
            await self._get_or_create_session(data.session_id, data.user_id)
            turn = Turn(
                session_id=data.session_id,
                user_id=data.user_id,
                messages=[m.model_dump() for m in data.messages],
                timestamp=data.timestamp,
                metadata_=data.metadata,
            )
            self.session.add(turn)
            await self.session.flush()
            await self.session.refresh(turn)
            return turn
        except SQLAlchemyError as e:
            log.error("turn_create_failed", session_id=data.session_id, error=str(e))
            raise

    async def delete_by_session(self, session_id: str) -> None:
        try:
            result = await self.session.execute(select(Session).where(Session.id == session_id))
            db_session = result.scalar_one_or_none()
            if db_session:
                await self.session.delete(db_session)
                await self.session.flush()
        except SQLAlchemyError as e:
            log.error("delete_by_session_failed", session_id=session_id, error=str(e))
            raise

    async def delete_by_user(self, user_id: str) -> None:
        try:
            result = await self.session.execute(select(Turn).where(Turn.user_id == user_id))
            for turn in result.scalars().all():
                await self.session.delete(turn)
            await self.session.flush()
        except SQLAlchemyError as e:
            log.error("delete_by_user_failed", user_id=user_id, error=str(e))
            raise
