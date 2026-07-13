"""6位不重复账号生成器"""
import random
from sqlalchemy.orm import Session
from models.user import User

def generate_unique_account(db: Session) -> str:
    """生成6位不重复数字账号"""
    for _ in range(100):
        account = str(random.randint(100000, 999999))
        existing = db.query(User).filter(User.account == account).first()
        if not existing:
            return account
    raise RuntimeError("无法生成唯一账号，请重试")
