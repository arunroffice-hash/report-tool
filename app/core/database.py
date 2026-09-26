from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import logging
import os

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

# Ensure database URL is set
database_url = settings.DATABASE_URL
if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set")

logger.info(f"Database URL: {database_url[:40]}...")

is_sqlite = database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    database_url,
    connect_args=connect_args,
    future=True,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Provide a database session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables() -> None:
    """Create all tables registered in the SQLAlchemy metadata."""
    try:
        from app.models.inventory import InventoryMaster
        from app.models.upload_history import UploadHistory
        from app.models.user import User

        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        raise


def seed_admin_user() -> None:
    """Create a default admin user for first-time startup."""
    try:
        from app.core.security import hash_password
        from app.models.user import User

        db = SessionLocal()
        try:
            existing_admin = db.query(User).filter(User.username == "admin").first()
            if not existing_admin:
                logger.info("Creating default admin user...")
                admin_user = User(
                    username="admin",
                    password_hash=hash_password("admin123"),
                    role="admin",
                )
                db.add(admin_user)
                db.commit()
                logger.info("✅ Admin user created successfully")
            else:
                logger.info("ℹ️ Admin user already exists")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"⚠️ Could not seed admin user (non-critical): {e}")
        # Don't crash - app can run without this
