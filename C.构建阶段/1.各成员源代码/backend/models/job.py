"""岗位模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    salary_range = Column(String(50), nullable=True)
    education_requirement = Column(String(20), nullable=True)
    work_experience_requirement = Column(Integer, nullable=True)
    fresh_requirement = Column(String(10), nullable=True)  # 应届 / 往届 / 不限
    work_content = Column(Text, nullable=True)
    position_requirements = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    applications = relationship("JobApplication", back_populates="job", cascade="all, delete-orphan")

class JobApplication(Base):
    __tablename__ = "job_applications"
    __table_args__ = (UniqueConstraint("job_id", "interviewee_id", name="uq_job_interviewee"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    interviewee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ai_note = Column(String(500), nullable=True)
    applied_at = Column(DateTime, server_default=func.now())

    job = relationship("Job", back_populates="applications")
    interviewee = relationship("User")
