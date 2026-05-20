from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: str
    mongodb_db_name: str = "vas"

    jwt_secret: str = ""
    jwt_refresh_secret: str = ""
    jwt_access_min: int = 15
    jwt_refresh_days: int = 7

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    environment: str = "development"
    rate_limit_login: str = "5/minute"
    detection_threshold: float = 0.85
    internal_api_key: str = ""
    cors_allowed_origins: str = "http://localhost:8080"
    metrics_allowed_ips: str = "127.0.0.1"


settings = Settings()