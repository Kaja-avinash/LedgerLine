"""Application configuration (loaded from environment / .env)."""

import os
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


def _build_url(prefix: str) -> str | None:
    user = os.getenv(f"DB_{prefix}_USER")
    if not user:
        return None
    password = os.getenv(f"DB_{prefix}_PASSWORD", "")
    host = os.getenv(f"DB_{prefix}_HOST", "localhost")
    port = os.getenv(f"DB_{prefix}_PORT", "5432")
    name = os.getenv(f"DB_{prefix}_NAME", "ledgerline_dev")
    return (
        f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url_app: str | None = None
    database_url_migrator: str | None = None
    db_app_user: str | None = None
    db_app_password: str | None = None
    db_app_host: str = "localhost"
    db_app_port: int = 5432
    db_app_name: str = "ledgerline_dev"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    @property
    def app_database_url(self) -> str:
        if self.db_app_user:
            from urllib.parse import quote_plus as qp

            pw = self.db_app_password or ""
            return (
                f"postgresql+psycopg://{qp(self.db_app_user)}:{qp(pw)}"
                f"@{self.db_app_host}:{self.db_app_port}/{self.db_app_name}"
            )
        if self.database_url_app:
            return self.database_url_app
        env_url = _build_url("APP")
        if env_url:
            return env_url
        raise RuntimeError("App database URL is not configured")


settings = Settings()
