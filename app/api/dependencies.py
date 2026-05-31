from typing import Annotated

from fastapi import Depends, Request

from app.infra.db.get_db import DatabaseAdapter
from app.infra.db.unit_of_work import UnitOfWork
from app.infra.llm.client import LLMClient
from app.services.embedding_service import EmbeddingService
from app.services.extraction_service import ExtractionService
from app.services.memory_service import MemoryService
from app.services.key_normalizer import KeyNormalizer
from app.services.recall import RecallService
from app.services.recall.assembler import ContextAssembler
from app.services.recall.expander import QueryExpander
from app.services.recall.searcher import HybridSearcher
from app.services.search_service import SearchService


def get_db_adapter(request: Request) -> DatabaseAdapter:
    return request.app.state.db


def get_uow(
    db: Annotated[DatabaseAdapter, Depends(get_db_adapter)],
) -> UnitOfWork:
    return UnitOfWork(db.session_factory)


UoWDep = Annotated[UnitOfWork, Depends(get_uow)]
DbAdapterDep = Annotated[DatabaseAdapter, Depends(get_db_adapter)]

_llm_client = LLMClient()

_embedding_service = EmbeddingService(_llm_client)
_extraction_service = ExtractionService(_llm_client)

_key_normalizer = KeyNormalizer(_llm_client)
_assembler = ContextAssembler(_llm_client)
_expander = QueryExpander(_llm_client)

_searcher = HybridSearcher(_embedding_service)


_memory_service = MemoryService(
    extraction_service=_extraction_service,
    embedding_service=_embedding_service,
    key_normalizer=_key_normalizer,
)

_recall_service = RecallService(
    expander=_expander,
    searcher=_searcher,
    assembler=_assembler,
)
_search_service = SearchService(searcher=_searcher)

def get_memory_service() -> MemoryService:
    return _memory_service


def get_recall_service() -> RecallService:
    return _recall_service


def get_search_service() -> SearchService:
    return _search_service


MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]
RecallServiceDep = Annotated[RecallService, Depends(get_recall_service)]
SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
