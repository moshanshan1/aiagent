"""岗位路由"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from schemas.job import JobCreate, JobUpdate
from services.job_service import create_job, get_jobs, get_job, update_job, delete_job, apply_job, get_applicants
from services.message_service import create_channel
from utils.security import get_current_user, require_interviewer
from models.user import User
from models.job import Job, JobApplication

router = APIRouter(prefix="/jobs", tags=["岗位"])

@router.post("", status_code=201)
def create(req: JobCreate, user: User = Depends(require_interviewer), db: Session = Depends(get_db)):
    job = create_job(db, user.id, req.dict())
    return {"code": 201, "data": _job_to_dict(job), "message": "ok"}

@router.get("")
def list_jobs(
    title: Optional[str] = None, education_requirement: Optional[str] = None,
    work_experience_requirement: Optional[int] = None, fresh_requirement: Optional[str] = None,
    sort: Optional[str] = "created_at", order: Optional[str] = "desc",
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    filters = {"title": title, "education_requirement": education_requirement,
               "work_experience_requirement": work_experience_requirement,
               "fresh_requirement": fresh_requirement, "sort": sort, "order": order}
    result = get_jobs(db, filters, page, size)
    items = []
    for job in result["items"]:
        d = _job_to_dict(job)
        if user.role == "interviewee":
            applied = db.query(JobApplication).filter(JobApplication.job_id == job.id, JobApplication.interviewee_id == user.id).first()
            d["has_applied"] = applied is not None
        items.append(d)
    return {"code": 200, "data": {"items": items, "total": result["total"], "page": page, "size": size}, "message": "ok"}

@router.get("/{job_id}")
def get_job_detail(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = get_job(db, job_id)
    d = _job_to_dict(job)
    if user.role == "interviewee":
        applied = db.query(JobApplication).filter(JobApplication.job_id == job.id, JobApplication.interviewee_id == user.id).first()
        d["has_applied"] = applied is not None
    return {"code": 200, "data": d, "message": "ok"}

@router.put("/{job_id}")
def update(job_id: int, req: JobUpdate, user: User = Depends(require_interviewer), db: Session = Depends(get_db)):
    job = get_job(db, job_id)
    updated = update_job(db, job, req.dict(exclude_unset=True), user)
    return {"code": 200, "data": _job_to_dict(updated), "message": "ok"}

@router.delete("/{job_id}")
def delete(job_id: int, user: User = Depends(require_interviewer), db: Session = Depends(get_db)):
    job = get_job(db, job_id)
    delete_job(db, job, user)
    return {"code": 200, "data": None, "message": "ok"}

@router.post("/{job_id}/apply", status_code=201)
def apply(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "interviewee":
        return {"code": 403, "data": None, "message": "仅面试者可报名岗位"}
    application = apply_job(db, job_id, user)
    return {"code": 201, "data": {"id": application.id}, "message": "报名成功"}

@router.get("/{job_id}/applicants")
def list_applicants(job_id: int, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
                    user: User = Depends(require_interviewer), db: Session = Depends(get_db)):
    job = get_job(db, job_id)
    if job.created_by != user.id:
        return {"code": 403, "data": None, "message": "仅创建者可查看意向面试者"}
    result = get_applicants(db, job_id, page, size)
    items = []
    for app in result["items"]:
        interviewee = db.query(User).filter(User.id == app.interviewee_id).first()
        items.append({
            "interviewee_id": interviewee.id, "name": interviewee.name,
            "education": interviewee.education, "work_experience": interviewee.work_experience,
            "is_fresh": interviewee.is_fresh, "skills": interviewee.skills,
            "ai_note": app.ai_note, "applied_at": app.applied_at
        })
    return {"code": 200, "data": {"items": items, "total": result["total"], "page": page, "size": size}, "message": "ok"}

@router.post("/{job_id}/applicants/{interviewee_id}/message-channel", status_code=201)
def create_msg_channel_from_applicants(job_id: int, interviewee_id: int,
                                       user: User = Depends(require_interviewer), db: Session = Depends(get_db)):
    channel = create_channel(db, user.id, interviewee_id, "意向仓库")
    return {"code": 201, "data": {"channel_id": channel.id}, "message": "通讯渠道已创建"}

def _job_to_dict(job):
    return {
        "id": job.id, "title": job.title, "salary_range": job.salary_range,
        "education_requirement": job.education_requirement,
        "work_experience_requirement": job.work_experience_requirement,
        "fresh_requirement": job.fresh_requirement, "work_content": job.work_content,
        "position_requirements": job.position_requirements, "created_by": job.created_by,
        "created_at": job.created_at, "updated_at": job.updated_at
    }