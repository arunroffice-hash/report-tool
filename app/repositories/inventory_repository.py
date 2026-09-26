from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session, Query

from app.models.inventory import InventoryMaster


class InventoryRepository:
    """Repository for inventory reads and bulk replace operations."""

    def get_filtered_query(
        self,
        db: Session,
        main_code: str | None = None,
        child_code: str | None = None,
        description: str | None = None,
    ) -> Query:
        query = db.query(InventoryMaster)

        if main_code:
            query = query.filter(InventoryMaster.main_code.ilike(f"%{main_code}%"))
        if child_code:
            query = query.filter(InventoryMaster.child_code.ilike(f"%{child_code}%"))
        if description:
            query = query.filter(InventoryMaster.description.ilike(f"%{description}%"))

        return query

    def count_filtered(self, db: Session, **filters: Any) -> int:
        return self.get_filtered_query(db, **filters).count()

    def replace_inventory_records(self, db: Session, rows: list[dict], batch_id: int) -> None:
        """Delete previous inventory and bulk insert the new batch."""
        db.query(InventoryMaster).delete(synchronize_session=False)
        records = [
            {
                "main_code": row["main_code"],
                "child_code": row["child_code"],
                "description": row["description"],
                "available_qty": row["available_qty"],
                "set_qty": row["set_qty"],
                "loose_qty": row["loose_qty"],
                "upload_batch_id": batch_id,
            }
            for row in rows
        ]
        if records:
            db.bulk_insert_mappings(InventoryMaster, records)

    def clear_inventory_records(self, db: Session) -> int:
        """Delete all uploaded inventory records from the master table."""
        deleted = db.query(InventoryMaster).delete(synchronize_session=False)
        db.commit()
        return deleted

    def get_paginated(self, db: Session, query: Query, page: int, per_page: int):
        offset = (page - 1) * per_page
        return query.offset(offset).limit(per_page).all()
