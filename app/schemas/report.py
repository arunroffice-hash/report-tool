from typing import Literal

from pydantic import BaseModel, Field


class ReportQuery(BaseModel):
    main_code: str | None = None
    child_code: str | None = None
    description: str | None = None
    sort_by: str = Field(default="main_code")
    sort_order: Literal["asc", "desc"] = "asc"
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=100, ge=1, le=100)
