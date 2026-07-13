"""面试模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from database import Base

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    interviewee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    interviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), nullable=False, default="未定时")  # 未定时/未开始/正在进行/已结束
    open_time_start = Column(DateTime, nullable=True)
    open_time_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    job = relationship("Job")
    interviewee = relationship("User", foreign_keys=[interviewee_id])
    interviewer = relationship("User", foreign_keys=[interviewer_id])
    questions = relationship("Question", back_populates="interview", cascade="all, delete-orphan", order_by="Question.sort_order")
    answers = relationship("Answer", back_populates="interview", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=True)  # 技术/行为/情景
    sort_order = Column(Integer, nullable=False)

    interview = relationship("Interview", back_populates="questions")

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    audio_path = Column(String(255), nullable=True)
    transcript = Column(Text, nullable=True)
    tone_features = Column(Text, nullable=True)  # JSON 存储语调特征
    content_analysis = Column(Text, nullable=True)
    answered_at = Column(DateTime, server_default=func.now())

    interview = relationship("Interview", back_populates="answers")
    question = relationship("Question")
