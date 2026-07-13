"""报告相关 Pydantic 模型"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReportResponse(BaseModel):
    id: int
    interview_id: int
    interviewee_name: Optional[str] = None
    job_title: Optional[str] = None
    answer_summary: Optional[str] = None
    highlights: Optional[str] = None
    risks: Optional[str] = None
    recommendation: Optional[str] = None
    skill_score: Optional[float] = None
    communication_score: Optional[float] = None
    logic_score: Optional[float] = None
    culture_score: Optional[float] = None
    interviewer_rating: Optional[str] = None
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RatingUpdate(BaseModel):
    rating: str  # S/A/B/C
