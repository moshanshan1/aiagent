"""认证相关 Pydantic 模型"""
from pydantic import BaseModel, Field
from typing import Optional

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=20)
    password: str = Field(..., min_length=6, max_length=50)

class LoginRequest(BaseModel):
    account: str
    password: str

class UserInfo(BaseModel):
    id: int
    account: str
    name: str
    role: str

class RegisterResponse(BaseModel):
    account: str
    name: str
    role: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo

class ProfileUpdate(BaseModel):
    education: Optional[str] = None
    work_experience: Optional[int] = None
    is_fresh: Optional[str] = None
    salary_expectation: Optional[str] = None
    skills: Optional[str] = None
    experience: Optional[str] = None

class ProfileResponse(UserInfo):
    education: Optional[str] = None
    work_experience: Optional[int] = None
    is_fresh: Optional[str] = None
    salary_expectation: Optional[str] = None
    skills: Optional[str] = None
    experience: Optional[str] = None
    avatar_url: Optional[str] = None
