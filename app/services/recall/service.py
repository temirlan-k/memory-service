from app.api.schemas.recall import RecallResponse
from app.infra.db.unit_of_work import UnitOfWork
from app.services.recall.assembler import ContextAssembler
from app.services.recall.expander import QueryExpander
from app.services.recall.searcher import HybridSearcher


class RecallService:
    def __init__(self, expander: QueryExpander, searcher: HybridSearcher, assembler: ContextAssembler):
        self._expander = expander
        self._searcher = searcher
        self._assembler = assembler

    async def recall(self, uow: UnitOfWork, query: str, user_id: str | None, max_tokens: int) -> RecallResponse:
        if not user_id:
            return RecallResponse(context="", citations=[])

        queries = await self._expander.expand(query)
        async with uow:
            candidates = await self._searcher.search(uow, user_id, query, queries)
            stable = await uow.memories.get_stable_facts(user_id)

        return await self._assembler.assemble(stable, candidates, max_tokens)
