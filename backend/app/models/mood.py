from sqlalchemy import Column, Integer, CheckConstraint, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid
from datetime import datetime, timezone
from app.models.base import Base

# Model: Represents the database table.

class MoodType(enum.Enum):
    happy = 'happy'
    sad = 'sad'
    anxious = 'anxious'
    angry = 'angry'
    neutral = 'neutral'
    tired = 'tired'
    stressed = 'stressed'
    depressed = 'depressed'

class Mood(Base):
    __tablename__ = "moods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=True)
    mood_type = Column(Enum(MoodType), nullable=True)
    intensity = Column(Integer, CheckConstraint('intensity BETWEEN 1 AND 10'), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="moods") 

# id = Column(Integer, primary_key=True, index=True)
# user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
