"""岗位相关 Pydantic 模型"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class JobCreate(BaseModel):
    title: str
    salary_range: Optional[str] = None
    education_requirement: Optional[str] = None
    work_experience_requirement: Optional[int] = None
    fresh_requirement: Optional[str] = None
    work_content: Optional[str] = None
    position_requirements: Optional[str] = None

class JobUpdate(BaseModel):
    title: Optional[str] = None
    salary_range: Optional[str] = None
    education_requirement: Optional[str] = None
    work_experience_requirement: Optional[int] = None
    fresh_requirement: Optional[str] = None
    work_content: Optional[str] = None
    position_requirements: Optional[str] = None

class JobResponse(BaseModel):
    id: int
    title: str
    salary_range: Optional[str] = None
    education_requirement: Optional[str] = None
    work_experience_requirement: Optional[int] = None
    fresh_requirement: Optional[str] = None
    work_content: Optional[str] = None
    position_requirements: Optional[str] = None
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    has_applied: Optional[bool] = None

    class Config:
        from_attributes = True

class ApplicantResponse(BaseModel):
    interviewee_id: int
    name: str
    education: Optional[str] = None
    work_experience: Optional[int] = None
    is_fresh: Optional[str] = None
    skills: Optional[str] = None
    ai_note: Optional[str] = None
    applied_at: datetime
