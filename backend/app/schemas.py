from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# ===== User Schemas =====
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# ===== TestCase Schemas =====
class TestCaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    method: str  # GET, POST, PUT, DELETE
    url: str
    headers: Optional[str] = "{}"
    body: Optional[str] = "{}"
    expected_status: int = 200


class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[str] = None
    body: Optional[str] = None
    expected_status: Optional[int] = None


class TestCaseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    method: str
    url: str
    headers: Optional[str]
    body: Optional[str]
    expected_status: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
