from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseSettings):
    jwt_secret_key: str | None = None

    aes_key: bytes | None = None
    key_length: ClassVar[int] = 32
    nonce_length: ClassVar[int] = 12

    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 3
    jwt_algorithm: str = "HS256"

    model_config = SettingsConfigDict(
        env_prefix="SECURITY__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )