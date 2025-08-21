from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from enum import Enum
from typing import Optional


class MoodTypeEnum(str, Enum):
    happy = 'happy'
    sad = 'sad'
    anxious = 'anxious'
    angry = 'angry'
    neutral = 'neutral'
    tired = 'tired'
    stressed = 'stressed'
    depressed = 'depressed'


class MoodBase(BaseModel):
    description: Optional[str] = None
    mood_type: Optional[MoodTypeEnum] = None
    intensity: Optional[int] = Field(None, ge=1, le=10)

class MoodCreate(MoodBase):
    # user_id: UUID
    date: datetime | None = None  # Optional custom date from frontend

class MoodUpdate(BaseModel):
    description: Optional[str] = None
    mood_type: Optional[MoodTypeEnum] = None  # Keep this optional for PATCH
    intensity: Optional[int] = Field(None, ge=1, le=10)


# Pydantic model used for output for API responses (e.g. returning mood data from the database)
class MoodOut(MoodBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
