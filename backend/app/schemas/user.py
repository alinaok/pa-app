from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserOut(UserBase):
    id: UUID

    class Config:
        from_attributes = True
