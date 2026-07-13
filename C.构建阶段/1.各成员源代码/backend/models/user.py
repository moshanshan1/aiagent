"""用户模型"""
from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account = Column(String(6), unique=True, nullable=False, index=True)
    name = Column(String(20), nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False, default="interviewee")  # interviewer / interviewee

    # 面试者个人信息
    education = Column(String(20), nullable=True)
    work_experience = Column(Integer, nullable=True)
    is_fresh = Column(String(10), nullable=True)  # 应届 / 往届
    salary_expectation = Column(String(30), nullable=True)
    skills = Column(String(500), nullable=True)
    experience = Column(String(2000), nullable=True)
    avatar_url = Column(String(255), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
