"""通讯相关 Pydantic 模型"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MessageSend(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)

class MessageResponse(BaseModel):
    id: int
    sender_type: str
    content: str
    sent_at: datetime

    class Config:
        from_attributes = True

class ChannelResponse(BaseModel):
    id: int
    interviewee: dict
    created_from: Optional[str] = None
    last_message: Optional[dict] = None
    created_at: datetime
