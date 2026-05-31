from app.api.schemas.search import SearchResponse, SearchResult
from app.infra.db.unit_of_work import UnitOfWork
from app.services.recall.searcher import HybridSearcher


class SearchService:
    def __init__(self, searcher: HybridSearcher):
        self._searcher = searcher

    async def search(self, uow: UnitOfWork, query: str, user_id: str | None, limit: int) -> SearchResponse:
        if not user_id:
            return SearchResponse(results=[])

        async with uow:
            candidates = await self._searcher.search(uow, user_id, query, [])
        results = [
            SearchResult(
                content=f"{m.key}: {m.value}",
                score=round(score, 4),
                session_id=m.source_session_id,
                timestamp=m.created_at,
                metadata={},
            )
            for m, score in candidates[:limit]
        ]
        return SearchResponse(results=results)
