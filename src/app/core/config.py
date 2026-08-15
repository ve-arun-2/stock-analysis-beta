"""
Application settings.

Centralizes all configuration in one typed object instead of scattering
`os.environ` calls across the codebase. Values are loaded from environment
variables (and a local `.env` file in development) via pydantic-settings.

Usage:
    from app.core.config import get_settings
    settings = get_settings()
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration, populated from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General
    app_name: str = "Stock Analysis Platform"
    app_env: str = "local"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/stock_analysis"

    # API
    cors_origins: str = "http://localhost:3000"

    # Data sources (Phase 1: config placeholders only, no logic wired up yet)
    watchlist_excel_path: str = "./data/watchlists/watchlist.xlsx"
    chartink_base_url: str = "https://chartink.com"
    yahoo_finance_base_url: str = "https://query1.finance.yahoo.com"

    # Logging
    log_level: str = "INFO"

    # Telegram bot (used by stock_monitor.py to send breakout alerts)
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # --- AWS S3 ---
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = ""
    S3_BUCKET_NAME: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins as a list, parsed from the comma-separated env value."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so the environment is parsed only once."""
    return Settings()


settings = get_settings()
