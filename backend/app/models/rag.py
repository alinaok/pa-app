from sqlalchemy import Column, Integer, String, DateTime
from app.models.base import Base
from datetime import datetime, UTC

class EmbeddedFile(Base):
    __tablename__ = "embedded_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)