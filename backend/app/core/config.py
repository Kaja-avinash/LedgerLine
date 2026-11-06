"""Application configuration (loaded from environment / .env)."""

import os
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


def _normalize_pg_url(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip()
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


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
    database_url: str | None = None
    postgres_url: str | None = None
    db_app_user: str | None = None
    db_app_password: str | None = None
    db_app_host: str = "localhost"
    db_app_port: int = 5432
    db_app_name: str = "ledgerline_dev"

    # JWT
    jwt_secret_key: str = ""
    secret_key: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    def model_post_init(self, __context: object) -> None:
        if not self.jwt_secret_key:
            self.jwt_secret_key = (
                self.secret_key
                or os.getenv("SECRET_KEY")
                or os.getenv("JWT_SECRET_KEY")
                or "ledgerline_default_secret_key_change_in_production"
            )

    @property
    def app_database_url(self) -> str:
        if self.db_app_user:
            from urllib.parse import quote_plus as qp

            pw = self.db_app_password or ""
            return (
                f"postgresql+psycopg://{qp(self.db_app_user)}:{qp(pw)}"
                f"@{self.db_app_host}:{self.db_app_port}/{self.db_app_name}"
            )
        candidate = (
            self.database_url_app
            or self.database_url
            or self.postgres_url
            or os.getenv("DATABASE_URL_APP")
            or os.getenv("DATABASE_URL")
            or os.getenv("POSTGRES_URL")
            or _build_url("APP")
        )
        normalized = _normalize_pg_url(candidate)
        if normalized:
            return normalized
        raise RuntimeError("App database URL is not configured")


settings = Settings()
