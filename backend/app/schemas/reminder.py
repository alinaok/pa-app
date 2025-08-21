from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum

class ReminderMethodEnum(str, Enum):
    push = "push"
    email = "email"
    sms = "sms"

class ReminderBase(BaseModel):
    title: str
    description: Optional[str] = None
    remind_at: datetime
    method: ReminderMethodEnum = ReminderMethodEnum.push

class ReminderCreate(ReminderBase):
    task_id: Optional[UUID] = None

class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    remind_at: Optional[datetime] = None
    method: Optional[ReminderMethodEnum] = None

class ReminderOut(ReminderBase):
    id: UUID
    user_id: UUID
    task_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True
