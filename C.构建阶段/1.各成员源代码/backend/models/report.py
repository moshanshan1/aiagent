"""面试报告模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, func
from sqlalchemy.orm import relationship
from database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), unique=True, nullable=False)
    interviewee_name = Column(String(20), nullable=True)
    job_title = Column(String(100), nullable=True)
    answer_summary = Column(Text, nullable=True)
    highlights = Column(Text, nullable=True)
    risks = Column(Text, nullable=True)
    recommendation = Column(String(200), nullable=True)

    skill_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    logic_score = Column(Float, nullable=True)
    culture_score = Column(Float, nullable=True)

    rating = Column(String(1), nullable=True)  # S/A/B/C
    interviewer_rating = Column(String(1), nullable=True)
    pdf_path = Column(String(255), nullable=True)

    generated_at = Column(DateTime, server_default=func.now())

    interview = relationship("Interview")
