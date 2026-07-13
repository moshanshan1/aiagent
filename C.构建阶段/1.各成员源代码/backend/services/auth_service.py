"""认证服务"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.user import User
from utils.security import hash_password, verify_password, create_access_token
from utils.account_generator import generate_unique_account

def register_interviewee(db: Session, name: str, password: str) -> dict:
    """注册面试者"""
    account = generate_unique_account(db)
    user = User(
        account=account,
        name=name,
        password_hash=hash_password(password),
        role="interviewee"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"account": user.account, "name": user.name, "role": user.role}

def login(db: Session, account: str, password: str) -> dict:
    """用户登录"""
    user = db.query(User).filter(User.account == account).first()
    if not user:
        raise HTTPException(status_code=401, detail="账号不存在")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="密码错误")
    token = create_access_token(user.id, user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 86400,
        "user": {
            "id": user.id,
            "account": user.account,
            "name": user.name,
            "role": user.role
        }
    }

def get_user_profile(user: User) -> dict:
    """获取用户信息"""
    return {
        "id": user.id,
        "account": user.account,
        "name": user.name,
        "role": user.role,
        "education": user.education,
        "work_experience": user.work_experience,
        "is_fresh": user.is_fresh,
        "salary_expectation": user.salary_expectation,
        "skills": user.skills,
        "experience": user.experience,
        "avatar_url": user.avatar_url
    }

def update_profile(db: Session, user: User, data: dict) -> dict:
    """更新面试者个人信息"""
    if user.role != "interviewee":
        raise HTTPException(status_code=403, detail="仅面试者可编辑个人信息")
    for key, value in data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return get_user_profile(user)