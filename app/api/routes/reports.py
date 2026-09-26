from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.export_service import ExportService
from app.services.report_service import ReportService

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
report_service = ReportService()
export_service = ExportService()


@router.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request, user: User = Depends(get_current_user)):
    """Render the reports workspace with filtering controls and data grid."""
    return templates.TemplateResponse(
        "reports.html",
        {"request": request, "user": user},
    )


@router.get("/review-sets", response_class=HTMLResponse)
async def review_sets_page(request: Request, user: User = Depends(get_current_user)):
    """Render the dedicated one-qty-short review workspace."""
    return templates.TemplateResponse(
        "review_sets.html",
        {"request": request, "user": user},
    )


@router.get("/api/reports")
async def get_reports(
    request: Request,
    main_code: str | None = Query(default=None),
    child_code: str | None = Query(default=None),
    description: str | None = Query(default=None),
    sort_by: str = Query(default="main_code"),
    sort_order: str = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return paginated inventory data for the reports grid, respecting current filters."""
    return report_service.get_report_data(
        db,
        main_code=main_code,
        child_code=child_code,
        description=description,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page,
    )


@router.get("/api/reports/export")
async def export_reports(
    request: Request,
    main_code: str | None = Query(default=None),
    child_code: str | None = Query(default=None),
    description: str | None = Query(default=None),
    sort_by: str = Query(default="main_code"),
    sort_order: str = Query(default="asc"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export the filtered inventory dataset to Excel while preserving the current query state."""
    buffer = export_service.export_excel(
        db,
        main_code=main_code,
        child_code=child_code,
        description=description,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="inventory_report.xlsx"',
        },
    )


@router.get("/api/reports/review")
async def get_review_sets(
    request: Request,
    main_code: str | None = Query(default=None),
    child_code: str | None = Query(default=None),
    description: str | None = Query(default=None),
    sort_by: str = Query(default="main_code"),
    sort_order: str = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return sets that are one unit short of completion for manual review."""
    return report_service.get_one_qty_short_review_data(
        db,
        main_code=main_code,
        child_code=child_code,
        description=description,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page,
    )


@router.get("/api/reports/review/export")
async def export_review_sets(
    request: Request,
    main_code: str | None = Query(default=None),
    child_code: str | None = Query(default=None),
    description: str | None = Query(default=None),
    sort_by: str = Query(default="main_code"),
    sort_order: str = Query(default="asc"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export the one-unit short review list to Excel."""
    buffer = report_service.export_one_qty_short_review_excel(
        db,
        main_code=main_code,
        child_code=child_code,
        description=description,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="one_qty_short_review.xlsx"',
        },
    )
