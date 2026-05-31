from app.infra.db.models.memory import Memory
from app.infra.db.unit_of_work import UnitOfWork
from app.services.embedding_service import EmbeddingService

_RRF_K = 60


def _rrf_score(ranks: list[int]) -> float:
    return sum(1 / (_RRF_K + r + 1) for r in ranks)


class HybridSearcher:
    def __init__(self, embedding_service: EmbeddingService):
        self._embedding = embedding_service

    async def search(self, uow: UnitOfWork, user_id: str, query: str, extra_queries: list[str]) -> list[tuple[Memory, float]]:
        all_queries = [query] + extra_queries
        query_embedding = (await self._embedding.embed_texts([query]))[0]

        bm25_cache: dict[str, list[Memory]] = {}
        bm25_ranks: dict[str, list[int]] = {}
        for q in all_queries:
            results = await uow.memories.search_bm25(user_id, q)
            bm25_cache[q] = results
            for rank, memory in enumerate(results):
                bm25_ranks.setdefault(str(memory.id), []).append(rank)

        vector_ranks: dict[str, list[int]] = {}
        vector_results = await uow.memories.search_vector(user_id, query_embedding)
        for rank, (memory, _) in enumerate(vector_results):
            vector_ranks.setdefault(str(memory.id), []).append(rank)

        memory_map: dict[str, Memory] = {str(m.id): m for m, _ in vector_results}
        for results in bm25_cache.values():
            for m in results:
                memory_map[str(m.id)] = m

        all_ids = set(bm25_ranks) | set(vector_ranks)
        rrf = {
            mid: _rrf_score(bm25_ranks.get(mid, [])) + _rrf_score(vector_ranks.get(mid, []))
            for mid in all_ids
        }

        ranked = sorted(all_ids, key=lambda mid: rrf[mid], reverse=True)
        return [(memory_map[mid], rrf[mid]) for mid in ranked if mid in memory_map]
