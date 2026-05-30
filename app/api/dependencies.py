from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request

from app.infra.db.get_db import DatabaseAdapter
from app.infra.db.unit_of_work import UnitOfWork
from app.services.memory_service import MemoryService


def get_db_adapter(request: Request) -> DatabaseAdapter:
    return request.app.state.db


async def get_uow(
    db: Annotated[DatabaseAdapter, Depends(get_db_adapter)],
) -> AsyncGenerator[UnitOfWork, None]:
    async with UnitOfWork(db.session_factory) as uow:
        yield uow


UoWDep = Annotated[UnitOfWork, Depends(get_uow)]

_memory_service = MemoryService()


def get_memory_service() -> MemoryService:
    return _memory_service


MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]
