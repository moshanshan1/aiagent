"""报告服务"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.report import Report
from models.interview import Interview, Answer, Question
from ai.assessor import assess_and_build_report, analyze_content
from utils.file_storage import save_report_pdf

def _calc_rating(skill: float, comm: float, logic: float, culture: float) -> str:
    """根据四维度分数自动计算综合评级（S/A/B/C）"""
    avg = (skill + comm + logic + culture) / 4
    if avg >= 90:
        return "S"
    if avg >= 80:
        return "A"
    if avg >= 70:
        return "B"
    return "C"

def generate_report(db: Session, interview_id: int, user) -> Report:
    """生成面试报告"""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")
    if interview.interviewer_id != user.id:
        raise HTTPException(status_code=403, detail="仅面试官可生成报告")
    if interview.status != "已结束":
        raise HTTPException(status_code=400, detail="面试尚未结束")
    
    existing = db.query(Report).filter(Report.interview_id == interview_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="报告已生成")
    
    answers = db.query(Answer).filter(Answer.interview_id == interview_id).all()
    answers_summary = ""
    for a in answers:
        q = db.query(Question).filter(Question.id == a.question_id).first()
        answers_summary += f"题目: {q.question_text if q else ''}\n回答: {a.transcript or '未转写'}\n语调: {a.tone_features or '未分析'}\n\n"
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(assess_and_build_report(
        interview.interviewee.name, interview.job.title, answers_summary))
    
    skill = result.get("skill_score", 0) or 0
    comm = result.get("communication_score", 0) or 0
    logic = result.get("logic_score", 0) or 0
    culture = result.get("culture_score", 0) or 0
    auto_rating = _calc_rating(skill, comm, logic, culture)

    report = Report(
        interview_id=interview_id,
        interviewee_name=interview.interviewee.name,
        job_title=interview.job.title,
        answer_summary=result.get("answer_summary"),
        highlights=result.get("highlights"),
        risks=result.get("risks"),
        recommendation=result.get("recommendation"),
        skill_score=skill,
        communication_score=comm,
        logic_score=logic,
        culture_score=culture,
        rating=auto_rating,  # 系统自动评级
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

def get_reports(db: Session, filters: dict, page: int, size: int) -> dict:
    """查询报告列表"""
    query = db.query(Report)
    if filters.get("job_id"):
        query = query.filter(Report.job_title.contains(str(filters["job_id"])))
    if filters.get("rating"):
        query = query.filter(Report.interviewer_rating == filters["rating"])
    if filters.get("interviewee_name"):
        query = query.filter(Report.interviewee_name.contains(filters["interviewee_name"]))
    
    sort_field = filters.get("sort", "generated_at")
    order = filters.get("order", "desc")
    sort_column = getattr(Report, sort_field, Report.generated_at)
    query = query.order_by(sort_column.desc() if order == "desc" else sort_column.asc())
    
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {"items": items, "total": total, "page": page, "size": size}

def get_report(db: Session, report_id: int) -> Report:
    """查询报告详情"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report

def rate_report(db: Session, report: Report, rating: str) -> Report:
    """对报告评级"""
    if rating not in ["S", "A", "B", "C"]:
        raise HTTPException(status_code=400, detail="评级必须为 S/A/B/C")
    report.interviewer_rating = rating
    db.commit()
    db.refresh(report)
    return report

def download_report(db: Session, report: Report) -> str:
    """下载报告 PDF"""
    if report.pdf_path:
        return report.pdf_path

    # 获取面试者详细信息
    interviewee = report.interview.interviewee if report.interview else None

    report_data = {
        "interviewee_name": report.interviewee_name,
        "job_title": report.job_title,
        "answer_summary": report.answer_summary,
        "highlights": report.highlights,
        "risks": report.risks,
        "recommendation": report.recommendation,
        "skill_score": report.skill_score,
        "communication_score": report.communication_score,
        "logic_score": report.logic_score,
        "culture_score": report.culture_score,
        "rating": report.rating,                       # 系统自动评级
        "interviewer_rating": report.interviewer_rating,  # 面试官手动评级
        # 面试者个人信息
        "education": interviewee.education if interviewee else None,
        "work_experience": interviewee.work_experience if interviewee else None,
        "is_fresh": interviewee.is_fresh if interviewee else None,
        "skills": interviewee.skills if interviewee else None,
        "salary_expectation": interviewee.salary_expectation if interviewee else None,
        "avatar_url": interviewee.avatar_url if interviewee else None,
    }
    path = save_report_pdf(report_data, report.id)
    report.pdf_path = path
    db.commit()
    return path