"""面试路由"""
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from schemas.interview import InterviewCreate, OpenTimeUpdate, QuestionUpdate
from services.interview_service import (create_interview, get_interviews, get_interview,
    update_open_time, update_question, check_in, get_answers)
from services.message_service import create_channel
from utils.security import get_current_user, require_interviewer, require_interviewee
from utils.file_storage import save_audio
from ai.tone_analyzer import analyze_tone
from ai.assessor import analyze_content
from models.user import User
from models.interview import Interview

router = APIRouter(prefix="/interviews", tags=["面试"])

@router.post("", status_code=201)
def create(req: InterviewCreate, user: User = Depends(require_interviewer), db: Session = Depends(get_db)):
    interview = create_interview(db, req.job_id, req.interviewee_id, user.id)
    return {"code": 201, "data": _interview_to_dict(interview), "message": "面试创建成功，AI已生成5道问题"}

@router.get("")
def list_interviews(
    status: Optional[str] = None, job_id: Optional[int] = None,
    sort: Optional[str] = "created_at", order: Optional[str] = "desc",
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    filters = {"status": status, "job_id": job_id, "sort": sort, "order": order}
    result = get_interviews(db, user, filters, page, size)
    items = [_interview_to_dict(i) for i in result["items"]]
    return {"code": 200, "data": {"items": items, "total": result["total"], "page": page, "size": size}, "message": "ok"}

@router.get("/{interview_id}")
def get_detail(interview_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    interview = get_interview(db, interview_id)
    return {"code": 200, "data": _interview_to_dict(interview), "message": "ok"}

@router.put("/{interview_id}/open-time")
def set_open_time(interview_id: int, req: OpenTimeUpdate, user: User = Depends(require_interviewer), db: Session = Depends(get_db)):
    interview = get_interview(db, interview_id)
    updated = update_open_time(db, interview, req.open_time_start, req.open_time_end, user)
    return {"code": 200, "data": _interview_to_dict(updated), "message": "ok"}

@router.put("/{interview_id}/questions/{question_id}")
def edit_question(interview_id: int, question_id: int, req: QuestionUpdate, user: User = Depends(require_interviewer), db: Session = Depends(get_db)):
    interview = get_interview(db, interview_id)
    q = update_question(db, interview, question_id, req.question_text, user)
    return {"code": 200, "data": {"id": q.id, "question_text": q.question_text}, "message": "ok"}

@router.get("/{interview_id}/check-in")
def checkin(interview_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    interview = get_interview(db, interview_id)
    data = check_in(db, interview, user)
    return {"code": 200, "data": data, "message": "可以进入面试"}

@router.post("/{interview_id}/answers", status_code=201)
async def submit_voice_answer(
    interview_id: int, audio_file: UploadFile = File(...), question_id: int = Form(...),
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    interview = get_interview(db, interview_id)
    audio_path = await save_audio(audio_file, interview_id, question_id)
    
    # 异步处理语音分析（Omni 一次调用完成转写 + 语调分析）
    tone_result = analyze_tone(audio_path)
    transcript = tone_result.get("transcript", "")
    import json
    tone_str = json.dumps(tone_result, ensure_ascii=False)
    
    from models.interview import Answer, Question
    answer = db.query(Answer).filter(Answer.interview_id == interview_id, Answer.question_id == question_id).first()
    if answer:
        answer.audio_path = audio_path
        answer.transcript = transcript
        answer.tone_features = tone_str
    else:
        answer = Answer(interview_id=interview_id, question_id=question_id, audio_path=audio_path,
                       transcript=transcript, tone_features=tone_str)
        db.add(answer)
    
    # 内容分析
    question = db.query(Question).filter(Question.id == question_id).first()
    if question and transcript:
        content_analysis = await analyze_content(question.question_text, transcript, tone_str)
        answer.content_analysis = content_analysis
    
    db.commit()

    # 检查是否全部答完（不重复创建 Answer）
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

    return {"code": 201, "data": {"answer_id": answer.id, "next_question": next_q_data}, "message": "回答已保存"}

@router.get("/{interview_id}/answers")
def list_answers(interview_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = get_answers(db, interview_id)
    return {"code": 200, "data": data, "message": "ok"}

@router.post("/{interview_id}/message-channel", status_code=201)
def create_msg_channel(interview_id: int, user: User = Depends(require_interviewer), db: Session = Depends(get_db)):
    interview = get_interview(db, interview_id)
    channel = create_channel(db, user.id, interview.interviewee_id, "面试")
    return {"code": 201, "data": {"channel_id": channel.id}, "message": "通讯渠道已创建"}

def _interview_to_dict(interview):
    return {
        "id": interview.id,
        "job": {"id": interview.job.id, "title": interview.job.title} if interview.job else {},
        "interviewee": {"id": interview.interviewee.id, "name": interview.interviewee.name} if interview.interviewee else {},
        "status": interview.status,
        "questions": [{"id": q.id, "question_text": q.question_text, "question_type": q.question_type, "sort_order": q.sort_order} for q in interview.questions],
        "open_time_start": interview.open_time_start,
        "open_time_end": interview.open_time_end
    }