"""AI 全模块测试 — 覆盖所有 5 个对外接口的调用链路 + fallback"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import LLM_API_KEY, DASHSCOPE_API_KEY

# ── 模拟数据 ──
JOB_INFO = {
    "title": "后端开发工程师",
    "education_requirement": "本科",
    "work_experience_requirement": 3,
    "fresh_requirement": "往届",
    "work_content": "负责后端 API 开发与维护，参与系统架构设计",
    "position_requirements": "精通 Python / FastAPI，熟悉 MySQL",
}

CANDIDATE_INFO = {
    "name": "张三",
    "education": "本科",
    "work_experience": 3,
    "is_fresh": "往届",
    "skills": "Python, FastAPI, MySQL, Docker",
    "experience": "3 年后端开发经验，主导过多个 Web 项目",
}

MOCK_TRANSCRIPT = "我在电商项目中负责订单服务开发，使用 FastAPI 构建 RESTful API，用 MySQL 存储订单数据。"

MOCK_TONE = json.dumps({
    "transcript": MOCK_TRANSCRIPT,
    "emotion_hint": "自信、有活力",
    "confidence": "自信",
    "emotion": "积极",
    "speed": "正常",
}, ensure_ascii=False)

ANSWERS_SUMMARY = (
    "题目: 请介绍一下你在最近一个项目中负责的核心模块及技术实现。\n"
    f"回答: {MOCK_TRANSCRIPT}\n"
    f"语调: {MOCK_TONE}\n\n"
    "题目: 你遇到过最复杂的技术难题是什么？\n"
    "回答: 双十一大促时通过 Sentinel 实现接口级别流控。\n"
    f"语调: {MOCK_TONE}\n\n"
    "题目: 请描述一次你与团队成员意见不合的经历。\n"
    "回答: 技术选型时我主张 gRPC，团队倾向 HTTP，我整理对比文档后团队采纳了我的方案。\n"
    f"语调: {MOCK_TONE}\n\n"
    "题目: 如果项目截止日期突然提前一周，你会如何调整？\n"
    "回答: 评估优先级，与 PM 确定核心功能范围，加班追赶进度。\n"
    f"语调: {MOCK_TONE}\n\n"
    "题目: 假设你需要快速学习一项新技术来完成项目任务。\n"
    "回答: 先看官方文档快速上手，通过小 demo 验证可行性。\n"
    f"语调: {MOCK_TONE}"
)


def sep(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def check_api_keys():
    sep("环境检查")
    for name, key in [("LLM_API_KEY", LLM_API_KEY), ("DASHSCOPE_API_KEY", DASHSCOPE_API_KEY)]:
        ok = bool(key) and not key.startswith("your-")
        print(f"  {name}: {'✅ 已配置' if ok else '❌ 未配置，将使用 fallback'}")


# ═══════════════════════════════════════════════
# 1. tone_analyzer
# ═══════════════════════════════════════════════
def test_tone_analyzer():
    sep("1. tone_analyzer.analyze_tone()")
    from ai.tone_analyzer import analyze_tone

    audio_path = Path(__file__).resolve().parent / "uploads" / "audios"
    mp3 = sorted(audio_path.glob("*.mp3"))
    wav = sorted(audio_path.glob("*.wav"))
    candidates = mp3 + wav

    if not candidates:
        print("  ⚠️  未找到测试音频文件，跳过")
        return None

    path = str(candidates[0])
    print(f"  音频: {Path(path).name}")
    result = analyze_tone(path)

    print(f"  转写:   {result.get('transcript', '')[:80]}")
    print(f"  感觉:   {result.get('emotion_hint', 'N/A')}")
    print(f"  自信度: {result.get('confidence', 'N/A')}")
    print(f"  情绪:   {result.get('emotion', 'N/A')}")
    print(f"  语速:   {result.get('speed', 'N/A')}")
    if "error" in result:
        print(f"  ⚠️  错误: {result['error']}")
    return result


# ═══════════════════════════════════════════════
# 2. question_generator.generate_questions()
# ═══════════════════════════════════════════════
async def test_generate_questions():
    sep("2. question_generator.generate_questions()")
    from ai.question_generator import generate_questions

    questions = await generate_questions(JOB_INFO, CANDIDATE_INFO)
    print(f"  题目数: {len(questions)}")
    for i, q in enumerate(questions, 1):
        print(f"  [{i}] ({q.get('question_type', '?')}) {q['question_text'][:70]}")
    return questions


# ═══════════════════════════════════════════════
# 3. question_generator.generate_applicant_note()
# ═══════════════════════════════════════════════
async def test_applicant_note():
    sep("3. question_generator.generate_applicant_note()")
    from ai.question_generator import generate_applicant_note

    note = await generate_applicant_note(JOB_INFO, CANDIDATE_INFO)
    print(f"  AI 备注: {note}")
    return note


# ═══════════════════════════════════════════════
# 4. assessor.analyze_content()
# ═══════════════════════════════════════════════
async def test_analyze_content():
    sep("4. assessor.analyze_content()")
    from ai.assessor import analyze_content

    question = "请介绍一下你在最近一个项目中负责的核心模块及技术实现。"
    result = await analyze_content(question, MOCK_TRANSCRIPT, MOCK_TONE)
    print(f"  分析结果: {result[:120]}")
    return result


# ═══════════════════════════════════════════════
# 5. assessor.assess_and_build_report()
# ═══════════════════════════════════════════════
async def test_assess_and_build_report():
    sep("5. assessor.assess_and_build_report()")
    from ai.assessor import assess_and_build_report

    report = await assess_and_build_report("张三", "后端开发工程师", ANSWERS_SUMMARY)
    print(f"  回答摘要: {report.get('answer_summary', 'N/A')[:60]}")
    print(f"  录用建议: {report.get('recommendation', 'N/A')}")
    print(f"  评分: 技能={report.get('skill_score')} "
          f"沟通={report.get('communication_score')} "
          f"逻辑={report.get('logic_score')} "
          f"文化={report.get('culture_score')}")

    output = Path(__file__).resolve().parent / "uploads" / "reports" / "test_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  报告已导出: {output}")
    return report


# ═══════════════════════════════════════════════
# main
# ═══════════════════════════════════════════════
async def main():
    print("\n🧪  AI 全模块测试")
    print(f"  LLM 模型: {getattr(__import__('config', fromlist=['LLM_MODEL']), 'LLM_MODEL', '?')}")
    print(f"  Omni 模型: {getattr(__import__('config', fromlist=['OMNI_MODEL']), 'OMNI_MODEL', '?')}")

    check_api_keys()
    tone_result = test_tone_analyzer()
    qs = await test_generate_questions()
    note = await test_applicant_note()
    ca = await test_analyze_content()
    report = await test_assess_and_build_report()

    sep("📊 测试汇总")
    results = [
        ("tone_analyzer.analyze_tone()",           tone_result is not None),
        ("question_generator.generate_questions()", len(qs) == 5 if qs else False),
        ("question_generator.generate_applicant_note()", bool(note)),
        ("assessor.analyze_content()",              bool(ca)),
        ("assessor.assess_and_build_report()",      bool(report)),
    ]
    passed = 0
    for name, ok in results:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
        if ok:
            passed += 1
    print(f"\n  {passed}/{len(results)} 项通过")
    sep("")

if __name__ == "__main__":
    asyncio.run(main())
