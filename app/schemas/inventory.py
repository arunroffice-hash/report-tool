from pydantic import BaseModel, Field


class InventoryRowCreate(BaseModel):
    main_code: str = Field(..., min_length=1)
    child_code: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    available_qty: float = 0.0
    set_qty: float = 0.0
    loose_qty: float = 0.0


class InventoryUploadSummary(BaseModel):
    total_records: int
    successful_records: int
    failed_records: int
    upload_time: str
    batch_id: int
    status: str
