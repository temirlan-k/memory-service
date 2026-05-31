import structlog

from app.infra.llm.client import LLMClient

log = structlog.get_logger()

_BATCH_SIZE = 64


class EmbeddingService:
    def __init__(self, llm_client: LLMClient):
        self._llm = llm_client

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        results: list[list[float]] = []
        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i: i + _BATCH_SIZE]
            try:
                response = await self._llm.create_embeddings(batch)
                results.extend(e.embedding for e in sorted(response.data, key=lambda e: e.index))
            except Exception as e:
                log.error("embedding_batch_failed", batch_start=i, total=len(texts), error=str(e))
                raise

        log.info("embedding_done", count=len(results))
        return results