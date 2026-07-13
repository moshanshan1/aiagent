"""安全工具: JWT + 密码哈希"""
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_SECONDS
from database import get_db
from models.user import User
import hashlib
import secrets

security_scheme = HTTPBearer()

def hash_password(password: str) -> str:
    """使用 pbkdf2_sha256 替代 bcrypt（避免版本兼容问题）"""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${hashed.hex()}"

def verify_password(plain: str, hashed: str) -> bool:
    """验证密码"""
    try:
        salt, hash_hex = hashed.split('$')
        new_hash = hashlib.pbkdf2_hmac('sha256', plain.encode(), salt.encode(), 100000)
        return new_hash.hex() == hash_hex
    except:
        return False

def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token无效或已过期")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user

def require_interviewer(user: User = Depends(get_current_user)) -> User:
    if user.role != "interviewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅面试官可执行此操作")
    return user

def require_interviewee(user: User = Depends(get_current_user)) -> User:
    if user.role != "interviewee":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅面试者可执行此操作")
    return user