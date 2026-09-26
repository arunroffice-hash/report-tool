from sqlalchemy import Column, DateTime, Integer, String, func

from app.core.database import Base


class UploadHistory(Base):
    """Tracks each inventory upload batch for traceability and rollback auditing."""

    __tablename__ = "upload_history"

    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    uploaded_by = Column(String(100), nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    total_records = Column(Integer, default=0, nullable=False)
    success_records = Column(Integer, default=0, nullable=False)
    failed_records = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="completed", nullable=False)
