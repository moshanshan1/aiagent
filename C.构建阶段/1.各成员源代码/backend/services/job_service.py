"""岗位服务"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.job import Job, JobApplication
from models.user import User
from ai.question_generator import generate_applicant_note

def create_job(db: Session, interviewer_id: int, data: dict) -> Job:
    """创建岗位"""
    job = Job(created_by=interviewer_id, **data)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def get_jobs(db: Session, filters: dict, page: int, size: int) -> dict:
    """查询岗位列表"""
    query = db.query(Job)
    if filters.get("title"):
        query = query.filter(Job.title.contains(filters["title"]))
    if filters.get("education_requirement"):
        query = query.filter(Job.education_requirement == filters["education_requirement"])
    if filters.get("work_experience_requirement"):
        query = query.filter(Job.work_experience_requirement >= filters["work_experience_requirement"])
    if filters.get("fresh_requirement"):
        query = query.filter(Job.fresh_requirement == filters["fresh_requirement"])
    
    sort_field = filters.get("sort", "created_at")
    order = filters.get("order", "desc")
    sort_column = getattr(Job, sort_field, Job.created_at)
    query = query.order_by(sort_column.desc() if order == "desc" else sort_column.asc())
    
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {"items": items, "total": total, "page": page, "size": size}

def get_job(db: Session, job_id: int) -> Job:
    """查询岗位详情"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return job

def update_job(db: Session, job: Job, data: dict, user: User) -> Job:
    """更新岗位"""
    if job.created_by != user.id:
        raise HTTPException(status_code=403, detail="仅创建者可修改此岗位")
    for key, value in data.items():
        if value is not None:
            setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job

def delete_job(db: Session, job: Job, user: User) -> None:
    """删除岗位"""
    if job.created_by != user.id:
        raise HTTPException(status_code=403, detail="仅创建者可删除此岗位")
    if job.applications:
        raise HTTPException(status_code=409, detail="该岗位已有面试者报名，无法删除")
    db.delete(job)
    db.commit()

def apply_job(db: Session, job_id: int, interviewee: User) -> JobApplication:
    """面试者报名岗位"""
    existing = db.query(JobApplication).filter(
        JobApplication.job_id == job_id,
        JobApplication.interviewee_id == interviewee.id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="已报名该岗位")
    
    job = get_job(db, job_id)
    # AI 生成备注（异步，这里简化为同步）
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    job_info = {
        "title": job.title,
        "education_requirement": job.education_requirement,
        "work_experience_requirement": job.work_experience_requirement,
        "fresh_requirement": job.fresh_requirement
    }
    candidate_info = {
        "name": interviewee.name,
        "education": interviewee.education,
        "work_experience": interviewee.work_experience,
        "is_fresh": interviewee.is_fresh,
        "skills": interviewee.skills
    }
    ai_note = loop.run_until_complete(generate_applicant_note(job_info, candidate_info))
    
    application = JobApplication(
        job_id=job_id,
        interviewee_id=interviewee.id,
        ai_note=ai_note
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application

def get_applicants(db: Session, job_id: int, page: int, size: int) -> dict:
    """获取意向面试者列表"""
    query = db.query(JobApplication).filter(JobApplication.job_id == job_id)
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {"items": items, "total": total, "page": page, "size": size}