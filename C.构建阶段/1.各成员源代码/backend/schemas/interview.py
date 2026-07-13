"""面试相关 Pydantic 模型"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class InterviewCreate(BaseModel):
    job_id: int
    interviewee_id: int

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    question_type: Optional[str] = None
    sort_order: int

    class Config:
        from_attributes = True

class InterviewResponse(BaseModel):
    id: int
    job: dict
    interviewee: dict
    status: str
    questions: List[QuestionResponse]
    open_time_start: Optional[datetime] = None
    open_time_end: Optional[datetime] = None

class OpenTimeUpdate(BaseModel):
    open_time_start: datetime
    open_time_end: datetime

class QuestionUpdate(BaseModel):
    question_text: str

class AnswerResponse(BaseModel):
    id: int
    question_id: int
    question_text: Optional[str] = None
    transcript: Optional[str] = None
    content_analysis: Optional[str] = None
    answered_at: Optional[datetime] = None

class AnswerListResponse(BaseModel):
    items: List[AnswerResponse]
    completed_count: int
    total_count: int
    all_completed: bool

class CheckInResponse(BaseModel):
    current_question: Optional[dict] = None
