"""Pydantic schemas for users."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = "ACCOUNT_HOLDER"
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    is_active: bool | None = None
    role: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
