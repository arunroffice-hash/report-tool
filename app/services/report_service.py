from io import BytesIO

from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.models.inventory import InventoryMaster
from app.repositories.inventory_repository import InventoryRepository
from app.services.set_calculation import find_one_qty_short_sets


class ReportService:
    """Fetch paginated, filtered inventory data and export it to Excel."""

    def __init__(self):
        self.inventory_repository = InventoryRepository()

    @staticmethod
    def _normalize_report_row(row: dict) -> dict:
        """Ensure standalone SKUs without child components show full set quantity."""
        main_code = str(row.get("main_code") or "").strip()
        child_code = str(row.get("child_code") or "").strip()
        available_qty = float(row.get("available_qty") or 0)
        set_qty = float(row.get("set_qty") or 0)
        loose_qty = float(row.get("loose_qty") or 0)

        if main_code and child_code and main_code == child_code:
            set_qty = available_qty
            loose_qty = 0

        return {
            "id": row.get("id"),
            "main_code": main_code,
            "child_code": child_code,
            "description": row.get("description") or "",
            "available_qty": available_qty,
            "set_qty": set_qty,
            "loose_qty": loose_qty,
        }

    @staticmethod
    def _coerce_sort_field(sort_by: str):
        allowed = {"main_code": InventoryMaster.main_code, "child_code": InventoryMaster.child_code, "description": InventoryMaster.description, "available_qty": InventoryMaster.available_qty, "set_qty": InventoryMaster.set_qty, "loose_qty": InventoryMaster.loose_qty}
        return allowed.get(sort_by, InventoryMaster.main_code)

    def get_report_data(
        self,
        db: Session,
        *,
        main_code: str | None = None,
        child_code: str | None = None,
        description: str | None = None,
        sort_by: str = "main_code",
        sort_order: str = "asc",
        page: int = 1,
        per_page: int = 100,
    ) -> dict:
        query = self.inventory_repository.get_filtered_query(
            db,
            main_code=main_code,
            child_code=child_code,
            description=description,
        )
        total_records = query.count()

        sort_expression = self._coerce_sort_field(sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_expression.desc())
        else:
            query = query.order_by(sort_expression.asc())

        rows = self.inventory_repository.get_paginated(db, query, page, per_page)
        items = [
            self._normalize_report_row(
                {
                    "id": row.id,
                    "main_code": row.main_code,
                    "child_code": row.child_code,
                    "description": row.description,
                    "available_qty": row.available_qty,
                    "set_qty": row.set_qty,
                    "loose_qty": row.loose_qty,
                }
            )
            for row in rows
        ]

        total_pages = max(1, (total_records + per_page - 1) // per_page) if total_records else 1
        return {
            "records": items,
            "total_records": total_records,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "showing": {
                "start": (page - 1) * per_page + 1 if total_records else 0,
                "end": min(page * per_page, total_records),
            },
        }

    def get_one_qty_short_review_data(
        self,
        db: Session,
        *,
        main_code: str | None = None,
        child_code: str | None = None,
        description: str | None = None,
        sort_by: str = "main_code",
        sort_order: str = "asc",
        page: int = 1,
        per_page: int = 100,
    ) -> dict:
        query = self.inventory_repository.get_filtered_query(
            db,
            main_code=main_code,
            child_code=child_code,
            description=description,
        )

        rows = [
            {
                "Item": row.child_code,
                "Description": row.description,
                "On Hand": row.available_qty,
            }
            for row in query.all()
        ]
        review_rows = find_one_qty_short_sets(rows)

        review_rows.sort(key=lambda row: str(row["main_code"]))
        if sort_by == "set_size":
            review_rows.sort(key=lambda row: row["set_size"], reverse=(sort_order.lower() == "desc"))
        elif sort_by == "description":
            review_rows.sort(key=lambda row: str(row["description"]), reverse=(sort_order.lower() == "desc"))
        elif sort_by == "short_component":
            review_rows.sort(key=lambda row: str(row["short_component"]), reverse=(sort_order.lower() == "desc"))
        else:
            review_rows.sort(key=lambda row: str(row["main_code"]), reverse=(sort_order.lower() == "desc"))

        total_records = len(review_rows)
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_rows = review_rows[start_index:end_index]

        total_pages = max(1, (total_records + per_page - 1) // per_page) if total_records else 1
        return {
            "records": paginated_rows,
            "total_records": total_records,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "showing": {
                "start": start_index + 1 if total_records else 0,
                "end": min(end_index, total_records),
            },
        }

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
        query = self.inventory_repository.get_filtered_query(
            db,
            main_code=main_code,
            child_code=child_code,
            description=description,
        )

        column = self._coerce_sort_field(sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

        rows = query.all()
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Inventory"
        worksheet.append(["Main Code", "Child Code", "Description", "Available Qty", "Set Qty", "Loose Qty"])

        for row in rows:
            normalized = ReportService._normalize_report_row(
                {
                    "main_code": row.main_code,
                    "child_code": row.child_code,
                    "description": row.description,
                    "available_qty": row.available_qty,
                    "set_qty": row.set_qty,
                    "loose_qty": row.loose_qty,
                }
            )
            worksheet.append([
                normalized["main_code"],
                normalized["child_code"],
                normalized["description"],
                normalized["available_qty"],
                normalized["set_qty"],
                normalized["loose_qty"],
            ])

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        return buffer

    def export_one_qty_short_review_excel(
        self,
        db: Session,
        *,
        main_code: str | None = None,
        child_code: str | None = None,
        description: str | None = None,
        sort_by: str = "main_code",
        sort_order: str = "asc",
    ) -> BytesIO:
        review_data = self.get_one_qty_short_review_data(
            db,
            main_code=main_code,
            child_code=child_code,
            description=description,
            sort_by=sort_by,
            sort_order=sort_order,
            page=1,
            per_page=100000,
        )

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "One Qty Short Review"
        worksheet.append(["Main Code", "Description", "Set Size", "Missing Qty", "Short Component", "Component Quantities"])

        for row in review_data["records"]:
            worksheet.append([
                row["main_code"],
                row["description"],
                row["set_size"],
                row["missing_qty"],
                row["short_component"],
                str(row["component_quantities"]),
            ])

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        return buffer
