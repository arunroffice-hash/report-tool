from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    PROJECT_NAME = os.getenv("APP_NAME", "Inventory Reporting Web App")
    VERSION = os.getenv("APP_VERSION", "1.0.0")
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-before-production")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inventory.db")
    DATABASE_URL_POSTGRESQL = os.getenv(
        "DATABASE_URL_POSTGRESQL",
        "postgresql+psycopg2://app_user:app_password@localhost:5432/inventory_db",
    )
    BASE_DIR = BASE_DIR
    STATIC_DIR = BASE_DIR / "app" / "static"
    TEMPLATES_DIR = BASE_DIR / "app" / "templates"


settings = Settings()
