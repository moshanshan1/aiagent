"""AI面试官与人才评估系统 - FastAPI 主入口"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import engine, Base
from models import User, Job, JobApplication, Interview, Question, Answer, Report, MessageChannel, Message
from routers import auth, jobs, interviews, reports, messages
from utils.security import hash_password

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建表 + 创建默认面试官"""
    Base.metadata.create_all(bind=engine)
    _seed_interviewers()
    yield

app = FastAPI(
    title="AI面试官与人才评估系统",
    description="基于 FastAPI 的后端 API 服务",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件 (上传目录)
upload_dir = Path(__file__).resolve().parent / "uploads"
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# 注册路由
app.include_router(auth.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(interviews.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(messages.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "AI面试官与人才评估系统 API 服务运行中", "version": "1.0.0"}

@app.get("/api/health")
def health():
    return {"code": 200, "data": {"status": "healthy"}, "message": "ok"}

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"code": 9999, "data": None, "message": f"服务器内部错误: {str(exc)}"})

def _seed_interviewers():
    """创建默认面试官账号"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.role == "interviewer").first()
        if not existing:
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
            print("已创建默认面试官账号: 000001/admin123, 000002/admin123")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)