"""通讯服务"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.message import MessageChannel, Message
from models.user import User

def create_channel(db: Session, interviewer_id: int, interviewee_id: int, created_from: str) -> MessageChannel:
    """创建通讯渠道"""
    existing = db.query(MessageChannel).filter(
        MessageChannel.interviewer_id == interviewer_id,
        MessageChannel.interviewee_id == interviewee_id
    ).first()
    if existing:
        return existing
    channel = MessageChannel(interviewer_id=interviewer_id, interviewee_id=interviewee_id, created_from=created_from)
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel

def get_channels(db: Session, user: User, page: int, size: int) -> dict:
    """查询通讯渠道列表"""
    if user.role == "interviewer":
        query = db.query(MessageChannel).filter(MessageChannel.interviewer_id == user.id)
    else:
        query = db.query(MessageChannel).filter(MessageChannel.interviewee_id == user.id)
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    result = []
    for ch in items:
        last_msg = db.query(Message).filter(Message.channel_id == ch.id).order_by(Message.sent_at.desc()).first()
        interviewee = db.query(User).filter(User.id == ch.interviewee_id).first()
        result.append({
            "id": ch.id,
            "interviewee": {"id": interviewee.id, "name": interviewee.name, "account": interviewee.account} if interviewee else {},
            "created_from": ch.created_from,
            "last_message": {"content": last_msg.content, "sent_at": last_msg.sent_at} if last_msg else None,
            "created_at": ch.created_at
        })
    return {"items": result, "total": total, "page": page, "size": size}

def get_messages(db: Session, channel_id: int, page: int, size: int) -> dict:
    """查询渠道内消息"""
    query = db.query(Message).filter(Message.channel_id == channel_id).order_by(Message.sent_at.asc())
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {"items": items, "total": total, "page": page, "size": size}

def send_message(db: Session, channel_id: int, user: User, content: str) -> Message:
    """发送消息"""
    channel = db.query(MessageChannel).filter(MessageChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="通讯渠道不存在")
    if user.role == "interviewer" and channel.interviewer_id != user.id:
        raise HTTPException(status_code=403, detail="无权限操作该渠道")
    if user.role == "interviewee" and channel.interviewee_id != user.id:
        raise HTTPException(status_code=403, detail="无权限操作该渠道")
    
    sender_type = "面试官" if user.role == "interviewer" else "面试者"
    msg = Message(channel_id=channel_id, sender_id=user.id, sender_type=sender_type, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg