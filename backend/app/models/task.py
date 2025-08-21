from sqlalchemy import Column, Text, Enum, ForeignKey, DateTime, func, Boolean, String, Integer, Time
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid
from app.models.base import Base


class TaskStatus(enum.Enum):
    pending = 'pending'
    completed = 'completed'
    cancelled = 'cancelled'

class RecurrencePattern(enum.Enum):
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.pending)
    due_date = Column(DateTime, nullable=True)
    preferred_time = Column(Time, nullable=True)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String, nullable=True)
    recurrence_interval = Column(Integer, default=1)
    recurrence_end_date = Column(DateTime, nullable=True)
    calendar_event_id = Column(String, nullable=True)

    reminders = relationship('Reminder', back_populates='task')
    user = relationship("User", back_populates="tasks")