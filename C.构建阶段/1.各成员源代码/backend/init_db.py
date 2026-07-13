"""数据库初始化脚本 - 创建 MySQL 数据库并初始化表结构"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text
from database import engine, Base
from models import User, Job, JobApplication, Interview, Question, Answer, Report, MessageChannel, Message
from utils.security import hash_password

def init_database():
    """创建所有表并插入默认数据"""
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成！")
    
    from database import SessionLocal
    db = SessionLocal()
    try:
        # 检查是否已有面试官
        existing = db.query(User).filter(User.role == "interviewer").first()
        if not existing:
            print("正在创建默认面试官账号...")
            interviewers = [
                {"account": "000001", "name": "王面试官", "password": "admin123"},
                {"account": "000002", "name": "李面试官", "password": "admin123"},
            ]
            for data in interviewers:
                user = User(
                    account=data["account"],
                    name=data["name"],
                    password_hash=hash_password(data["password"]),
                    role="interviewer"
                )
                db.add(user)
            db.commit()
            print("默认面试官账号创建完成:")
            print("  账号: 000001  密码: admin123  姓名: 王面试官")
            print("  账号: 000002  密码: admin123  姓名: 李面试官")
        else:
            print("面试官账号已存在，跳过初始化。")
    finally:
        db.close()
    
    print("\n数据库初始化完成！")
    print("启动服务: python main.py  或  uvicorn main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    init_database()