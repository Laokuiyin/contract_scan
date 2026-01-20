from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class ReviewRecordBase(BaseModel):
    field_name: str = Field(..., description="字段名称")
    ai_value: Optional[str] = Field(None, description="AI提取的值")
    human_value: Optional[str] = Field(None, description="人工确认的值")
    is_correct: Optional[bool] = Field(None, description="AI提取是否正确")
    notes: Optional[str] = Field(None, description="备注")

class ReviewRecordCreate(ReviewRecordBase):
    reviewer: str = Field(..., description="审核人")

class ReviewRecordUpdate(BaseModel):
    human_value: Optional[str] = None
    is_correct: Optional[bool] = None
    notes: Optional[str] = None

class ReviewRecordResponse(ReviewRecordBase):
    id: UUID
    contract_id: UUID
    reviewer: str
    review_time: datetime

    model_config = ConfigDict(from_attributes=True)

class ReviewSummary(BaseModel):
    contract_id: UUID
    total_reviews: int
    pending_reviews: int
    completed_reviews: int
    accuracy_rate: Optional[float] = None
