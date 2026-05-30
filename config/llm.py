from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    llm_api_key: str | None = None
    llm_base_url: str = "https://openrouter.ai/api/v1"

    model_config = SettingsConfigDict(
        env_prefix="AI__", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
