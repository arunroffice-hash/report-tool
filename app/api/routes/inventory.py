import asyncio
import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.repositories.inventory_repository import InventoryRepository
from app.services.upload_service import InventoryUploadService

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@router.get("/master-uploader", response_class=HTMLResponse)
async def master_uploader_page(request: Request, user: User = Depends(get_current_user)):
    """Render the master uploader page for inventory replacement uploads."""
    return templates.TemplateResponse(
        "master_uploader.html",
        {"request": request, "user": user},
    )


@router.post("/api/inventory/clear")
async def clear_inventory(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete all uploaded inventory data so the user can start with a clean master set."""
    try:
        deleted_count = InventoryRepository().clear_inventory_records(db)
        return {
            "status": "cleared",
            "deleted_records": deleted_count,
            "message": "Master inventory cleared successfully.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/api/inventory/upload")
async def upload_inventory(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Upload an Excel file, validate mandatory columns, and replace inventory data in bulk."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files are allowed")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
    try:
        contents = await file.read()
        temp_file.write(contents)
        temp_file.close()

        try:
            service = InventoryUploadService()
            summary = await asyncio.to_thread(service.process_upload, temp_file.name, user.username)
            return summary
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if os.path.exists(temp_file.name):
            try:
                os.remove(temp_file.name)
            except PermissionError:
                pass
