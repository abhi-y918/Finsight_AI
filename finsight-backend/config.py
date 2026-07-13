# config.py
# ─────────────────────────────────────────────────────────────────
# Central place for ALL configuration and environment variables.
# We use python-dotenv to load values from a .env file.
# This way secrets (like API keys) never get hardcoded in code.
#
# HOW TO USE:
#   from config import settings
#   print(settings.ANTHROPIC_API_KEY)
# ─────────────────────────────────────────────────────────────────

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()  # reads .env file from project root


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────
    APP_NAME: str = "FinSight AI"
    DEBUG: bool = True

    # ── OpenRouter API ───────────────────────────────────────────
    # Get this from openrouter.ai
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    AI_MODEL: str = "anthropic/claude-3.5-sonnet"

    # ── File Upload ──────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: list = [".pdf", ".csv"]

    # ── Phase 2+ ─────────────────────────────────────────────────
    # DATABASE_URL: str = "postgresql://user:pass@localhost/finsight"
    # REDIS_URL: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"
        extra = "ignore"


# Single instance used everywhere
settings = Settings()