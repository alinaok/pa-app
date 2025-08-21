from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class SymptomBase(BaseModel):
    description: str


class SymptomCreate(SymptomBase):
    # user_id: UUID
    description: str
    date: datetime | None = None  # Optional custom date from frontend

class SymptomUpdate(BaseModel):
    description: str

class SymptomOut(SymptomBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
