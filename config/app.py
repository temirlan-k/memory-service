from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    app_name: str = "Memory Service"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 4
    reload: bool = True
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="APP__", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )