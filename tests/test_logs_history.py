from app.core.database import Base, SessionLocal, engine
from app.models.upload_history import UploadHistory
from app.repositories.upload_history_repository import UploadHistoryRepository


def test_upload_history_repository_get_all_returns_latest_first():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(UploadHistory).delete()

        repo = UploadHistoryRepository()
        repo.create_batch(
            db,
            file_name="first.xlsx",
            uploaded_by="admin",
            total_records=10,
            success_records=8,
            failed_records=2,
            status="completed",
        )
        repo.create_batch(
            db,
            file_name="second.xlsx",
            uploaded_by="admin",
            total_records=20,
            success_records=18,
            failed_records=2,
            status="completed",
        )
        db.commit()

        rows = repo.get_all(db)

        assert [row.file_name for row in rows] == ["second.xlsx", "first.xlsx"]
    finally:
        db.close()
