from sqlalchemy.orm import Session

from app.models.upload_history import UploadHistory


class UploadHistoryRepository:
    """Repository for upload batch history and audit metadata."""

    def create_batch(self, db: Session, *, file_name: str, uploaded_by: str, total_records: int, success_records: int, failed_records: int, status: str) -> UploadHistory:
        history = UploadHistory(
            file_name=file_name,
            uploaded_by=uploaded_by,
            total_records=total_records,
            success_records=success_records,
            failed_records=failed_records,
            status=status,
        )
        db.add(history)
        db.flush()
        return history

    def update_batch_status(self, db: Session, batch_id: int, *, status: str, total_records: int, success_records: int, failed_records: int) -> None:
        record = db.query(UploadHistory).filter(UploadHistory.batch_id == batch_id).first()
        if record:
            record.status = status
            record.total_records = total_records
            record.success_records = success_records
            record.failed_records = failed_records
            db.add(record)

    def get_all(self, db: Session) -> list[UploadHistory]:
        return db.query(UploadHistory).order_by(UploadHistory.batch_id.desc()).all()

    def get_latest(self, db: Session) -> UploadHistory | None:
        return db.query(UploadHistory).order_by(UploadHistory.batch_id.desc()).first()
