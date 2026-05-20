from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=100)


class UserOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    email: EmailStr
    full_name: str
    role: str
    created_at: datetime


class UserDB(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    hashed_password: str
    full_name: str
    role: str = "operator"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)