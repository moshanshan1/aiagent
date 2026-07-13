"""报告路由"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from schemas.report import RatingUpdate
from services.report_service import generate_report, get_reports, get_report, rate_report, download_report
from services.message_service import create_channel
from utils.security import get_current_user, require_interviewer
from models.user import User

router = APIRouter(prefix="/reports", tags=["报告"])

@router.post("/{interview_id}/generate", status_code=201)
def gen_report(interview_id: int, user: User = Depends(require_interviewer), db: Session = Depends(get_db)):
    report = generate_report(db, interview_id, user)
    return {"code": 201, "data": _report_to_dict(report), "message": "报告生成成功"}

@router.get("")
def list_reports(
    job_id: Optional[int] = None, rating: Optional[str] = None,
    interviewee_name: Optional[str] = None, sort: Optional[str] = "generated_at",
    order: Optional[str] = "desc", page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    filters = {"job_id": job_id, "rating": rating, "interviewee_name": interviewee_name, "sort": sort, "order": order}
    result = get_reports(db, filters, page, size)
    items = [_report_to_dict(r) for r in result["items"]]
    return {"code": 200, "data": {"items": items, "total": result["total"], "page": page, "size": size}, "message": "ok"}

@router.get("/{report_id}")
def get_detail(report_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = get_report(db, report_id)
    return {"code": 200, "data": _report_to_dict(report), "message": "ok"}

@router.put("/{report_id}/rating")
def rate(report_id: int, req: RatingUpdate, user: User = Depends(require_interviewer), db: Session = Depends(get_db)):
    report = get_report(db, report_id)
    updated = rate_report(db, report, req.rating)
    return {"code": 200, "data": _report_to_dict(updated), "message": "ok"}

@router.get("/{report_id}/download")
def download(report_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = get_report(db, report_id)
    path = download_report(db, report)
    return FileResponse(path, media_type="application/pdf", filename=f"report_{report_id}.pdf")

@router.post("/{report_id}/message-channel", status_code=201)
def create_msg_channel(report_id: int, user: User = Depends(require_interviewer), db: Session = Depends(get_db)):
    report = get_report(db, report_id)
    from models.interview import Interview
    interview = db.query(Interview).filter(Interview.id == report.interview_id).first()
    channel = create_channel(db, user.id, interview.interviewee_id, "报告")
    return {"code": 201, "data": {"channel_id": channel.id}, "message": "通讯渠道已创建"}

def _report_to_dict(report):
    return {
        "id": report.id, "interview_id": report.interview_id,
        "interviewee_name": report.interviewee_name, "job_title": report.job_title,
        "answer_summary": report.answer_summary, "highlights": report.highlights,
        "risks": report.risks, "recommendation": report.recommendation,
        "skill_score": report.skill_score, "communication_score": report.communication_score,
        "logic_score": report.logic_score, "culture_score": report.culture_score,
        "rating": report.rating, "interviewer_rating": report.interviewer_rating, "generated_at": report.generated_at
    }