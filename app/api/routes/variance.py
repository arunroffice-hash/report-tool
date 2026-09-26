import logging
from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.repositories.upload_history_repository import UploadHistoryRepository
from app.services.variance_service import generate_variance_workbook, _read_sheet_map

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
logger = logging.getLogger("app.api.routes.variance")


@router.get("/variance", response_class=HTMLResponse)
async def variance_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("variance_calculator.html", {"request": request, "user": user})


@router.post("/api/variance")
async def variance_process(
    old_file: UploadFile = File(...),
    new_file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept two uploaded Excel files and return a generated comparison Excel."""
    # Log filenames and content types for debugging
    logger.info("Received variance upload: old_file=%s (%s), new_file=%s (%s)", old_file.filename, old_file.content_type, new_file.filename, new_file.content_type)

    # Use underlying file objects (spooled) for streaming read by openpyxl
    old_f = old_file.file
    new_f = new_file.file
    # ensure file pointers are at start (UploadFile may have non-zero position)
    try:
        old_f.seek(0)
    except Exception:
        pass
    try:
        new_f.seek(0)
    except Exception:
        pass
    # Optionally record an upload batch in the DB for auditability
    try:
        # read maps to estimate counts (seek before each read)
        try:
            old_f.seek(0)
        except Exception:
            pass
        old_map = _read_sheet_map(old_f)
        try:
            new_f.seek(0)
        except Exception:
            pass
        new_map = _read_sheet_map(new_f)

        repo = UploadHistoryRepository()
        batch = repo.create_batch(
            db,
            file_name=f"{old_file.filename} vs {new_file.filename}",
            uploaded_by=getattr(user, "username", "unknown"),
            total_records=max(len(old_map), len(new_map)),
            success_records=len(new_map),
            failed_records=0,
            status="completed",
        )
        db.commit()
    except Exception:
        # record creation should not block report generation
        logger.exception("Failed to record upload history")

    # rewind files and generate workbook
    try:
        old_f.seek(0)
    except Exception:
        pass
    try:
        new_f.seek(0)
    except Exception:
        pass

    buffer = generate_variance_workbook(old_f, new_f)
    try:
        size = buffer.getbuffer().nbytes
        logger.info("Generated variance workbook size: %d bytes", size)
    except Exception:
        logger.info("Generated variance workbook (size unknown)")

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="variance_report.xlsx"'},
    )
