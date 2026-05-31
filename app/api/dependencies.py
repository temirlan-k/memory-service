from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request

from app.infra.db.get_db import DatabaseAdapter
from app.infra.db.unit_of_work import UnitOfWork
from app.infra.llm.client import LLMClient
from app.services.embedding_service import EmbeddingService
from app.services.extraction_service import ExtractionService
from app.services.memory_service import MemoryService


def get_db_adapter(request: Request) -> DatabaseAdapter:
    return request.app.state.db


async def get_uow(
    db: Annotated[DatabaseAdapter, Depends(get_db_adapter)],
) -> AsyncGenerator[UnitOfWork, None]:
    async with UnitOfWork(db.session_factory) as uow:
        yield uow


UoWDep = Annotated[UnitOfWork, Depends(get_uow)]

_llm_client = LLMClient()
_memory_service = MemoryService(
    extraction_service=ExtractionService(_llm_client),
    embedding_service=EmbeddingService(_llm_client),
)


def get_memory_service() -> MemoryService:
    return _memory_service


MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]
