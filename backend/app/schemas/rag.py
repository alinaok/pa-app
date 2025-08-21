from pydantic import BaseModel
from datetime import datetime

class EmbeddedFileBase(BaseModel):
    filename: str

class EmbeddedFileCreate(EmbeddedFileBase):
    pass

class EmbeddedFileOut(EmbeddedFileBase):
    id: int
    uploaded_at: datetime
    class Config:
        orm_mode = True