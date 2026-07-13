"""文件存储工具"""
import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from config import AVATAR_DIR, AUDIO_DIR, REPORT_DIR, MAX_AVATAR_SIZE, MAX_AUDIO_SIZE

ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/jpg"}
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/mpeg", "audio/mp3", "audio/m4a", "audio/x-m4a", "audio/mp4"}

async def save_avatar(file: UploadFile, account: str) -> str:
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise ValueError("仅支持 jpg/png 格式头像")
    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE:
        raise ValueError("头像文件大小不能超过 2MB")
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    ext = "jpg" if "jpeg" in file.content_type or "jpg" in file.content_type else "png"
    filename = f"{account}.{ext}"
    filepath = AVATAR_DIR / filename
    with open(filepath, "wb") as f:
        f.write(content)
    return f"/uploads/avatars/{filename}"

async def save_audio(file: UploadFile, interview_id: int, question_id: int) -> str:
    content = await file.read()
    if len(content) > MAX_AUDIO_SIZE:
        raise ValueError("录音文件大小不能超过 10MB")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "wav"
    filename = f"interview_{interview_id}_q{question_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = AUDIO_DIR / filename
    with open(filepath, "wb") as f:
        f.write(content)
    return str(filepath)

def _find_cn_font(pdf) -> str | None:
    """查找系统中文字体，返回字体名称；找不到返回 None"""
    # 1. 项目目录下的 NotoSansSC
    local = Path(__file__).resolve().parent / "NotoSansSC-VariableFont_wght.ttf"
    if local.exists():
        pdf.add_font("NotoSansSC", "", str(local), uni=True)
        return "NotoSansSC"
    # 2. Windows 系统字体
    candidates = [
        (r"C:\Windows\Fonts\msyh.ttc", "YaHei"),
        (r"C:\Windows\Fonts\simsun.ttc", "SimSun"),
        (r"C:\Windows\Fonts\simhei.ttf", "SimHei"),
    ]
    for path, name in candidates:
        if Path(path).exists():
            try:
                pdf.add_font(name, "", path, uni=True)
                return name
            except Exception:
                continue
    return None


def save_report_pdf(report_data: dict, report_id: int) -> str:
    """使用 fpdf2 生成面试报告 PDF

    Args:
        report_data: {
            "interviewee_name", "job_title", "answer_summary",
            "highlights", "risks", "recommendation",
            "skill_score", "communication_score", "logic_score", "culture_score",
            "interviewer_rating"
        }
        report_id: 报告 ID（用于文件名）

    Returns:
        PDF 文件的绝对路径
    """
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = REPORT_DIR / f"report_{report_id}.pdf"

    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()

    cn_font = _find_cn_font(pdf)
    if not cn_font:
        # 无中文字体，降级为 HTML
        html_path = filepath.with_suffix(".html")
        edu = report_data.get('education') or '未填写'
        exp = report_data.get('work_experience')
        exp_str = f"{int(exp)}年" if exp is not None else "未填写"
        fresh = report_data.get('is_fresh') or '未填写'
        salary = report_data.get('salary_expectation') or '未填写'
        skills = report_data.get('skills') or '未填写'
        avatar = report_data.get('avatar_url') or ''

        html_parts = [
            "<html><head><meta charset='utf-8'><title>面试报告</title></head><body>",
            ('<img src="' + avatar + '" width=100>') if avatar else '',
            "<h1>面试评估报告</h1>",
            f"<p><b>面试者:</b> {report_data.get('interviewee_name')}</p>",
            f"<p><b>应聘岗位:</b> {report_data.get('job_title')}</p>",
            f"<p><b>学历:</b> {edu}  |  <b>经验:</b> {exp_str}  |  {fresh}</p>",
            f"<p><b>期望薪资:</b> {salary}</p>",
            f"<p><b>技能:</b> {skills}</p>",
            f"<h2>回答摘要</h2><p>{report_data.get('answer_summary', '无')}</p>",
            f"<h2>亮点</h2><p>{report_data.get('highlights', '无')}</p>",
            f"<h2>风险点</h2><p>{report_data.get('risks', '无')}</p>",
            f"<h2>录用建议</h2><p>{report_data.get('recommendation', '无')}</p>",
            "<h2>评分</h2><ul>",
            *[f"<li>{k}: {report_data.get(k, '未评分')}</li>"
              for k in ("skill_score", "communication_score", "logic_score", "culture_score")],
            "</ul>",
            f"<p><b>系统评级:</b> {report_data.get('rating') or '待计算'}  |  <b>面试官评级:</b> {report_data.get('interviewer_rating') or '未评级'}</p>",
            "</body></html>",
        ]
        html_path.write_text("\n".join(html_parts), encoding="utf-8")
        print("[INFO] 未找到中文字体，已生成 HTML 替代")
        return str(html_path)

    # ── 标题 ──
    pdf.set_font(cn_font, "", 20)
    pdf.cell(0, 15, "面试评估报告", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # ── 个人头像 ──
    from config import BASE_DIR
    avatar_url = report_data.get("avatar_url")
    if avatar_url:
        avatar_path = BASE_DIR / avatar_url.lstrip("/")
        if avatar_path.exists():
            try:
                pdf.image(str(avatar_path), x=160, y=12, w=30, h=30)
            except Exception:
                pass

    # ── 基本信息 ──
    pdf.set_font(cn_font, "", 11)
    name = report_data.get("interviewee_name", "未知")
    job_title = report_data.get("job_title", "未知")
    edu = report_data.get("education") or "未填写"
    exp = report_data.get("work_experience")
    exp_str = f"{int(exp)}年" if exp is not None else "未填写"
    fresh = report_data.get("is_fresh") or "未填写"
    salary = report_data.get("salary_expectation") or "未填写"
    skills = report_data.get("skills") or "未填写"

    pdf.cell(0, 8, f"面试者: {name}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"应聘岗位: {job_title}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"学历: {edu}  |  工作经验: {exp_str}  |  {fresh}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"期望薪资: {salary}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(cn_font, "", 10)
    pdf.cell(0, 8, f"技能: {skills}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # ── 各部分 ──
    sections = [
        ("一、回答摘要", report_data.get("answer_summary")),
        ("二、亮点", report_data.get("highlights")),
        ("三、风险点", report_data.get("risks")),
        ("四、录用建议", report_data.get("recommendation")),
    ]
    for title, content in sections:
        pdf.set_font(cn_font, "", 13)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(cn_font, "", 10)
        pdf.multi_cell(0, 6, content or "无")
        pdf.ln(3)

    # ── 评分 ──
    pdf.set_font(cn_font, "", 13)
    pdf.cell(0, 10, "五、评分", new_x="LMARGIN", new_y="NEXT")
    scores = [
        ("专业技能", "skill_score"),
        ("沟通能力", "communication_score"),
        ("逻辑思维", "logic_score"),
        ("文化匹配", "culture_score"),
    ]
    pdf.set_font(cn_font, "", 10)
    for label, key in scores:
        score = report_data.get(key)
        pdf.cell(40, 8, label)
        bar_w = min(float(score or 0) / 100 * 80, 80)
        pdf.set_fill_color(76, 129, 190)
        pdf.cell(bar_w, 8, "", fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(80 - bar_w, 8, "")
        pdf.cell(0, 8, f"  {score}" if score is not None else "  未评分",
                 new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # ── 评级 ──
    auto_rating = report_data.get("rating")
    manual_rating = report_data.get("interviewer_rating")
    pdf.set_font(cn_font, "", 11)
    pdf.cell(0, 8, f"系统评级: {auto_rating if auto_rating else '待计算'}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"面试官评级: {manual_rating if manual_rating else '未评级'}",
             new_x="LMARGIN", new_y="NEXT")

    # ── 页脚 ──
    pdf.ln(10)
    pdf.set_font(cn_font, "", 8)
    from datetime import date
    pdf.cell(0, 6, f"生成日期: {date.today().isoformat()}", align="C",
             new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(filepath))
    return str(filepath)
