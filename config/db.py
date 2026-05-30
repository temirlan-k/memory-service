from typing import Any, Dict
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    host: str = "postgres"
    port: int = 5432
    name: str = "postgres"
    user: str = "postgres"
    password: str = "postgres"

    engine_kwargs: Dict[str, Any] = Field(
        default_factory=lambda: {
            "echo": False,
            "future": True,
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800,
        }
    )

    session_kwargs: Dict[str, Any] = Field(
        default_factory=lambda: {
            "autoflush": False,
            "autocommit": False,
            "expire_on_commit": False,
        }
    )

    @property
    def url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

    model_config = SettingsConfigDict(
        env_prefix="DB__", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )