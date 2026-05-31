from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    llm_api_key: str | None = None
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "openai/gpt-4o-mini"

    embedding_api_key: str | None = None
    embedding_base_url: str = "https://openrouter.ai/api/v1"
    embedding_model: str = "openai/text-embedding-3-small"

    model_config = SettingsConfigDict(
        env_prefix="AI__", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def resolved_embedding_api_key(self) -> str | None:
        return self.embedding_api_key or self.llm_api_key
