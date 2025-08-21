from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime, time
from enum import Enum
from app.schemas.reminder import ReminderOut

# mirrors SQLAlchemy TaskStatus enum but is used for API validation and docs.
class TaskStatusEnum(str, Enum):
    pending = 'pending'
    in_progress = 'in_progress'
    completed = 'completed'
    cancelled = 'cancelled'

class RecurrencePatternEnum(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"  # or use a Literal/Enum
    due_date: Optional[datetime] = None
    preferred_time: Optional[time] = None  # Add this new field
    is_recurring: bool = False
    recurrence_pattern: Optional[RecurrencePatternEnum] = None  # "daily", "weekly", "monthly"
    recurrence_interval: Optional[int] = 1
    recurrence_end_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    preferred_time: Optional[time] = None  # Add this new field
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    recurrence_interval: Optional[int] = None
    recurrence_end_date: Optional[datetime] = None

class TaskOut(TaskBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    completed_at: Optional[datetime] = None  # Add this field

    class Config:
        from_attributes = True


