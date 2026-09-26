from io import BytesIO

from sqlalchemy.orm import Session

from app.services.report_service import ReportService


class ExportService:
    """Thin wrapper around the report service to keep Excel export responsibilities isolated."""

    def __init__(self):
        self.report_service = ReportService()

    def export_excel(
        self,
        db: Session,
        *,
        main_code: str | None = None,
        child_code: str | None = None,
        description: str | None = None,
        sort_by: str = "main_code",
        sort_order: str = "asc",
    ) -> BytesIO:
        return self.report_service.export_excel(
            db,
            main_code=main_code,
            child_code=child_code,
            description=description,
            sort_by=sort_by,
            sort_order=sort_order,
        )
