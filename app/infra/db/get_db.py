from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from config.db import DBSettings


class DatabaseAdapter:
    def __init__(self, settings: DBSettings) -> None:
        self._engine: AsyncEngine = create_async_engine(settings.url, **settings.engine_kwargs)
        self.session_factory = async_sessionmaker(self._engine, **settings.session_kwargs)

    async def healthcheck(self) -> bool:
        async with self.session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True

    async def close(self) -> None:
        await self._engine.dispose()
