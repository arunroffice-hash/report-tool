from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.repositories.upload_history_repository import UploadHistoryRepository

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Render upload and processing history for the Logs module."""
    repository = UploadHistoryRepository()
    history_records = repository.get_all(db)

    formatted_rows = []
    for record in history_records:
        upload_date = record.upload_date
        if isinstance(upload_date, datetime):
            upload_date_label = upload_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            upload_date_label = str(upload_date)

        formatted_rows.append(
            {
                "batch_id": record.batch_id,
                "file_name": record.file_name,
                "uploaded_by": record.uploaded_by,
                "upload_date": upload_date_label,
                "total_records": record.total_records,
                "success_records": record.success_records,
                "failed_records": record.failed_records,
                "status": record.status,
                "log_summary": (
                    f"Processed {record.total_records} rows | "
                    f"Success {record.success_records} | "
                    f"Failed {record.failed_records} | "
                    f"Status: {record.status}"
                ),
            }
        )

    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
            "user": user,
            "history_records": formatted_rows,
        },
    )
