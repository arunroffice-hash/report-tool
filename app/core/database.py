from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

Base = declarative_base()

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, future=True)
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
    from app.models.inventory import InventoryMaster
    from app.models.upload_history import UploadHistory
    from app.models.user import User

    Base.metadata.create_all(bind=engine)


def seed_admin_user() -> None:
    """Create a default admin user for first-time startup."""
    from app.core.security import hash_password
    from app.models.user import User

    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            admin_user = User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin",
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()
