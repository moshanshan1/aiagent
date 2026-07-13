"""通讯路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas.message import MessageSend
from services.message_service import get_channels, get_messages, send_message
from utils.security import get_current_user
from models.user import User

router = APIRouter(prefix="/messages", tags=["通讯"])

@router.get("/channels")
def list_channels(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = get_channels(db, user, page, size)
    return {"code": 200, "data": result, "message": "ok"}

@router.get("/channels/{channel_id}")
def list_messages(channel_id: int, page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=100),
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = get_messages(db, channel_id, page, size)
    items = [{"id": m.id, "sender_type": m.sender_type, "content": m.content, "sent_at": m.sent_at} for m in result["items"]]
    return {"code": 200, "data": {"items": items, "total": result["total"], "page": page, "size": size}, "message": "ok"}

@router.post("/channels/{channel_id}", status_code=201)
def send(channel_id: int, req: MessageSend, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msg = send_message(db, channel_id, user, req.content)
    return {"code": 201, "data": {"id": msg.id, "sender_type": msg.sender_type, "content": msg.content, "sent_at": msg.sent_at}, "message": "发送成功"}