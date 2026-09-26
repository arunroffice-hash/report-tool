from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, func

from app.core.database import Base


class InventoryMaster(Base):
    """Primary inventory table storing row-level stock records."""

    __tablename__ = "inventory_master"
    __table_args__ = (
        Index("ix_inventory_master_main_code", "main_code"),
        Index("ix_inventory_master_child_code", "child_code"),
        Index("ix_inventory_master_description", "description"),
    )

    id = Column(Integer, primary_key=True, index=True)
    main_code = Column(String(100), nullable=False)
    child_code = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    available_qty = Column(Float, nullable=False, default=0.0)
    set_qty = Column(Float, nullable=False, default=0.0)
    loose_qty = Column(Float, nullable=False, default=0.0)
    upload_batch_id = Column(Integer, ForeignKey("upload_history.batch_id"), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
