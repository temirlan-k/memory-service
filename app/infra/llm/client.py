import instructor
import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel

from config import llm_settings

log = structlog.get_logger()


class LLMClient:
    def __init__(self):
        base = AsyncOpenAI(
            api_key=llm_settings.llm_api_key or "not-configured",
            base_url=llm_settings.llm_base_url,
        )
        self._client = instructor.from_openai(base, mode=instructor.Mode.TOOLS)
        self._embed_client = AsyncOpenAI(
            api_key=llm_settings.resolved_embedding_api_key or "not-configured",
            base_url=llm_settings.embedding_base_url,
        )

    async def extract(self, messages: list[dict], response_model: type[BaseModel]) -> BaseModel:
        return await self._client.chat.completions.create(
            model=llm_settings.llm_model,
            messages=messages,
            response_model=response_model,
            temperature=0,
        )

    async def create_embeddings(self, texts: list[str], model: str | None = None):
        return await self._embed_client.embeddings.create(
            model=model or llm_settings.embedding_model,
            input=texts,
        )
