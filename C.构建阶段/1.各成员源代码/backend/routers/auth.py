"""认证路由"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from schemas.auth import RegisterRequest, LoginRequest, ProfileUpdate
from services.auth_service import register_interviewee, login, get_user_profile, update_profile
from utils.security import get_current_user
from utils.file_storage import save_avatar
from models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    data = register_interviewee(db, req.name, req.password)
    return {"code": 201, "data": data, "message": "注册成功，请妥善保管您的账号"}

@router.post("/login")
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    data = login(db, req.account, req.password)
    return {"code": 200, "data": data, "message": "ok"}

@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    data = get_user_profile(user)
    return {"code": 200, "data": data, "message": "ok"}

@router.put("/me/profile")
def update_me_profile(req: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = req.dict(exclude_unset=True)
    result = update_profile(db, user, data)
    return {"code": 200, "data": result, "message": "ok"}

@router.post("/me/avatar")
async def upload_avatar(avatar: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        url = await save_avatar(avatar, user.account)
        user.avatar_url = url
        db.commit()
        return {"code": 200, "data": {"avatar_url": url}, "message": "ok"}
    except ValueError as e:
        return {"code": 400, "data": None, "message": str(e)}