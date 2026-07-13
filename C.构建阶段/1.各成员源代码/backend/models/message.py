"""通讯模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from database import Base

class MessageChannel(Base):
    __tablename__ = "message_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    interviewee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_from = Column(String(50), nullable=True)  # 意向仓库/面试/报告
    created_at = Column(DateTime, server_default=func.now())

    interviewer = relationship("User", foreign_keys=[interviewer_id])
    interviewee = relationship("User", foreign_keys=[interviewee_id])
    messages = relationship("Message", back_populates="channel", cascade="all, delete-orphan", order_by="Message.sent_at")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(Integer, ForeignKey("message_channels.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_type = Column(String(20), nullable=False)  # 面试官/面试者
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, server_default=func.now())

    channel = relationship("MessageChannel", back_populates="messages")
    sender = relationship("User")
