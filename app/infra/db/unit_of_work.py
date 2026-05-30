import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infra.db.repositories.turn_repo import TurnRepository

log = structlog.get_logger()


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> "UnitOfWork":
        self.session: AsyncSession = self._session_factory()
        self.turns = TurnRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            log.error("transaction_rolled_back", error=str(exc_val))
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()
