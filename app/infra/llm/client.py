import structlog
from openai import AsyncOpenAI

from config import llm_settings

log = structlog.get_logger()


class LLMClient:
    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=llm_settings.llm_api_key,
            base_url=llm_settings.llm_base_url,
        )
        self._embed_client = AsyncOpenAI(
            api_key=llm_settings.resolved_embedding_api_key,
            base_url=llm_settings.embedding_base_url,
        )

    async def chat_completion(self, messages: list[dict], model: str | None = None):
        response = await self._client.chat.completions.create(
            model=model or llm_settings.llm_model,
            messages=messages,
            temperature=0,
        )
        log.info("llm_response", response=response.model_dump())
        return response

    async def create_embeddings(self, texts: list[str], model: str | None = None):
        return await self._embed_client.embeddings.create(
            model=model or llm_settings.embedding_model,
            input=texts,
        )
