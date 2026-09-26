from sqlalchemy import Column, DateTime, Integer, String, func

from app.core.database import Base


class User(Base):
    """Application users with a role-based access model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="admin")
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
