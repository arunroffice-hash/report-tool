from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


def _normalize_database_url(database_url: str | None) -> str:
    if not database_url:
        return "sqlite:///./inventory.db"

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg2://", 1)

    if database_url.startswith("postgresql://") and "+" not in database_url.split("://", 1)[0]:
        return database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    return database_url


class Settings:
    PROJECT_NAME = os.getenv("APP_NAME", "Inventory Reporting Web App")
    VERSION = os.getenv("APP_VERSION", "1.0.0")
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-before-production")
    
    # Railway provides DATABASE_URL automatically, fallback to PostgreSQL or SQLite
    DATABASE_URL = _normalize_database_url(
        os.getenv(
            "DATABASE_URL",
            os.getenv(
                "DATABASE_URL_POSTGRESQL",
                "sqlite:///./inventory.db"
            )
        )
    )
    
    BASE_DIR = BASE_DIR
    STATIC_DIR = BASE_DIR / "app" / "static"
    TEMPLATES_DIR = BASE_DIR / "app" / "templates"


settings = Settings()
