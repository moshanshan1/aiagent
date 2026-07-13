"""面试服务"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from models.interview import Interview, Question, Answer
from models.job import Job
from models.user import User
from ai.question_generator import generate_questions


def _refresh_interview_status(db: Session, interview: Interview):
    """根据当前时间自动刷新面试状态"""
    now = datetime.now()
    if interview.status == "已结束":
        return
    if interview.open_time_start and interview.open_time_end:
        if now >= interview.open_time_end:
            interview.status = "已结束"
            db.commit()
        elif interview.open_time_start <= now < interview.open_time_end:
            if interview.status == "未开始":
                interview.status = "正在进行"
                db.commit()


def create_interview(db: Session, job_id: int, interviewee_id: int, interviewer_id: int) -> dict:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    interviewee = db.query(User).filter(User.id == interviewee_id).first()
    if not interviewee:
        raise HTTPException(status_code=404, detail="面试者不存在")

    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    job_info = {"title": job.title, "education_requirement": job.education_requirement,
                "work_experience_requirement": job.work_experience_requirement,
                "work_content": job.work_content, "position_requirements": job.position_requirements}
    candidate_info = {"name": interviewee.name, "education": interviewee.education,
                      "work_experience": interviewee.work_experience,
                      "skills": interviewee.skills, "experience": interviewee.experience}

    questions_data = loop.run_until_complete(generate_questions(job_info, candidate_info))

    interview = Interview(job_id=job_id, interviewee_id=interviewee_id,
                          interviewer_id=interviewer_id, status="未定时")
    db.add(interview)
    db.flush()

    for i, q in enumerate(questions_data, 1):
        question = Question(interview_id=interview.id, question_text=q["question_text"],
                           question_type=q.get("question_type", "技术"), sort_order=i)
        db.add(question)
    db.commit()
    db.refresh(interview)
    return interview


def get_interviews(db: Session, user: User, filters: dict, page: int, size: int) -> dict:
    query = db.query(Interview)
    if user.role == "interviewer":
        query = query.filter(Interview.interviewer_id == user.id)
    else:
        query = query.filter(Interview.interviewee_id == user.id)
        query = query.filter(Interview.status != "未定时")

    if filters.get("status"):
        query = query.filter(Interview.status == filters["status"])
    if filters.get("job_id"):
        query = query.filter(Interview.job_id == filters["job_id"])

    sort_field = filters.get("sort", "created_at")
    order = filters.get("order", "desc")
    sort_column = getattr(Interview, sort_field, Interview.created_at)
    query = query.order_by(sort_column.desc() if order == "desc" else sort_column.asc())

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()

    # 自动刷新每条面试的状态
    for interview in items:
        _refresh_interview_status(db, interview)

    return {"items": items, "total": total, "page": page, "size": size}


def get_interview(db: Session, interview_id: int) -> Interview:
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")
    _refresh_interview_status(db, interview)
    return interview


def update_open_time(db: Session, interview: Interview, start: datetime, end: datetime, user: User) -> Interview:
    if interview.interviewer_id != user.id:
        raise HTTPException(status_code=403, detail="仅面试官可设置开放时间")
    interview.open_time_start = start
    interview.open_time_end = end
    if interview.status == "未定时":
        interview.status = "未开始"
    db.commit()
    db.refresh(interview)
    return interview


def update_question(db: Session, interview: Interview, question_id: int, text: str, user: User) -> Question:
    if interview.interviewer_id != user.id:
        raise HTTPException(status_code=403, detail="仅面试官可修改问题")
    if interview.status not in ["未定时", "未开始"]:
        raise HTTPException(status_code=400, detail="仅未定时或未开始状态可修改问题")
    question = db.query(Question).filter(Question.id == question_id, Question.interview_id == interview.id).first()
    if not question:
        raise HTTPException(status_code=404, detail="问题不存在")
    question.question_text = text
    db.commit()
    db.refresh(question)
    return question


def check_in(db: Session, interview: Interview, user: User) -> dict:
    if interview.interviewee_id != user.id:
        raise HTTPException(status_code=403, detail="非本面试者")

    now = datetime.now()

    # 超过截止时间，自动结束
    if interview.open_time_end and now >= interview.open_time_end:
        interview.status = "已结束"
        db.commit()
        raise HTTPException(status_code=403, detail="面试已结束")

    if interview.status == "已结束":
        raise HTTPException(status_code=403, detail="面试已结束")

    if interview.status != "正在进行":
        if interview.open_time_start and interview.open_time_end:
            if interview.open_time_start <= now < interview.open_time_end:
                interview.status = "正在进行"
                db.commit()
            else:
                raise HTTPException(status_code=403, detail="面试尚未开放")
        else:
            raise HTTPException(status_code=403, detail="面试尚未开放")

    completed = db.query(Answer).filter(Answer.interview_id == interview.id).count()
    total = len(interview.questions)
    if completed >= total:
        raise HTTPException(status_code=403, detail="您已完成所有题目")

    next_q = interview.questions[completed] if completed < total else None
    return {"current_question": {"id": next_q.id, "question_text": next_q.question_text,
                                  "total_questions": total, "current_index": completed + 1} if next_q else None}


def submit_answer(db: Session, interview: Interview, question_id: int, audio_path: str, user: User) -> dict:
    if interview.interviewee_id != user.id:
        raise HTTPException(status_code=403, detail="非本面试者")
    question = db.query(Question).filter(Question.id == question_id, Question.interview_id == interview.id).first()
    if not question:
        raise HTTPException(status_code=404, detail="问题不存在")

    answer = Answer(interview_id=interview.id, question_id=question_id, audio_path=audio_path)
    db.add(answer)
    db.commit()
    db.refresh(answer)

    completed = db.query(Answer).filter(Answer.interview_id == interview.id).count()
    total = len(interview.questions)

    next_q = None
    if completed < total:
        next_q = interview.questions[completed]
        next_q_data = {"id": next_q.id, "question_text": next_q.question_text,
                       "current_index": completed + 1, "total_questions": total}
    else:
        interview.status = "已结束"
        db.commit()
        next_q_data = None

    return {"answer_id": answer.id, "next_question": next_q_data}


def get_answers(db: Session, interview_id: int) -> dict:
    answers = db.query(Answer).filter(Answer.interview_id == interview_id).all()
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    total = len(interview.questions) if interview else 0
    completed = len([a for a in answers if a.transcript])
    items = []
    for a in answers:
        q = db.query(Question).filter(Question.id == a.question_id).first()
        items.append({"id": a.id, "question_id": a.question_id,
                      "question_text": q.question_text if q else None,
                      "transcript": a.transcript, "content_analysis": a.content_analysis,
                      "answered_at": a.answered_at})
    return {"items": items, "completed_count": completed, "total_count": total,
            "all_completed": completed >= total}