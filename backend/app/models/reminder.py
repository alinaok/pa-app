from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid
from app.models.base import Base

class ReminderMethod(enum.Enum):
    push = 'push'
    email = 'email'
    sms = 'sms'

class Reminder(Base):
    __tablename__ = 'reminders'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    remind_at = Column(DateTime, nullable=False)
    method = Column(Enum(ReminderMethod), default=ReminderMethod.push)
    created_at = Column(DateTime, default=func.now())

    task = relationship('Task', back_populates='reminders')
    user = relationship("User", back_populates="reminders")
