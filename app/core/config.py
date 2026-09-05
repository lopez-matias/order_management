from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "NODO - Client & Order Management")
    environment: str = os.getenv("ENVIRONMENT", "development")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://gestion:gestion@localhost:5432/gestion_comercial",
    )
    secret_key: str = os.getenv("SECRET_KEY", "development-only-secret")


@lru_cache
def get_settings() -> Settings:
    return Settings()
