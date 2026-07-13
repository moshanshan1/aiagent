"""AI 面试问题生成器"""
import json
import asyncio
from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from ai.prompts import QUESTION_GENERATION_PROMPT, APPLICANT_AI_NOTE_PROMPT

# 全局 OpenAI 客户端
_client = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
        )
    return _client

async def _call_llm(prompt: str) -> str:
    """调用 LLM（OpenAI 兼容格式），成功返回响应文本，失败抛出 RuntimeError"""
    if not LLM_API_KEY or LLM_API_KEY.startswith("your-"):
        raise RuntimeError("API Key 未配置")
    try:
        client = _get_client()
        def sync_call():
            resp = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return resp.choices[0].message.content or ""
        return await asyncio.to_thread(sync_call)
    except Exception as e:
        err = str(e)
        if "timeout" in err.lower() or "timed out" in err.lower():
            raise RuntimeError("模型调用超时")
        if "401" in err or "Unauthorized" in err:
            raise RuntimeError("API Key 无效")
        if "429" in err or "Rate limit" in err:
            raise RuntimeError("请求频率超限")
        raise RuntimeError(f"模型调用异常: {err}")

def _fallback_questions() -> str:
    return json.dumps([
        {"question_text": "请介绍一下你在最近一个项目中负责的核心模块及技术实现。", "question_type": "技术"},
        {"question_text": "你遇到过最复杂的技术难题是什么？你是如何解决的？", "question_type": "技术"},
        {"question_text": "请描述一次你与团队成员意见不合的经历，你是如何处理的？", "question_type": "行为"},
        {"question_text": "如果项目截止日期突然提前一周，你会如何调整工作计划？", "question_type": "情景"},
        {"question_text": "假设你需要快速学习一项新技术来完成项目任务，你会怎么做？", "question_type": "情景"},
    ], ensure_ascii=False)

async def generate_questions(job_info: dict, candidate_info: dict) -> list:
    prompt = QUESTION_GENERATION_PROMPT.format(
        job_title=job_info.get("title", ""),
        education=job_info.get("education_requirement", "不限"),
        work_exp=job_info.get("work_experience_requirement", 0),
        work_content=job_info.get("work_content", ""),
        position_req=job_info.get("position_requirements", ""),
        name=candidate_info.get("name", ""),
        candidate_edu=candidate_info.get("education", "未填写"),
        candidate_exp=candidate_info.get("work_experience", 0),
        skills=candidate_info.get("skills", "未填写"),
        experience=candidate_info.get("experience", "未填写"),
    )
    try:
        result = await _call_llm(prompt)
    except RuntimeError as e:
        print(f"[WARN] question_generator: 模型调用错误 - {e}，使用 fallback 数据")
        return json.loads(_fallback_questions())

    try:
        start = result.find("[")
        end = result.rfind("]") + 1
        if start < 0 or end <= start:
            print("[WARN] question_generator: 返回格式异常（未找到 JSON 数组），使用 fallback 数据")
            print(f"  [原始响应前200字符]: {result[:200]}")
            return json.loads(_fallback_questions())
        questions = json.loads(result[start:end])
        if len(questions) != 5:
            print(f"[WARN] question_generator: 返回格式异常（题目数={len(questions)}，期望5道），使用 fallback 数据")
            return json.loads(_fallback_questions())
        return questions
    except json.JSONDecodeError as e:
        print(f"[WARN] question_generator: 返回格式异常（JSON 解析失败 - {e}），使用 fallback 数据")
        print(f"  [原始响应前200字符]: {result[:200]}")
        return json.loads(_fallback_questions())

async def generate_applicant_note(job_info: dict, candidate_info: dict) -> str:
    prompt = APPLICANT_AI_NOTE_PROMPT.format(
        job_title=job_info.get("title", ""),
        education_req=job_info.get("education_requirement", "不限"),
        work_exp_req=job_info.get("work_experience_requirement", 0),
        fresh_req=job_info.get("fresh_requirement", "不限"),
        name=candidate_info.get("name", ""),
        education=candidate_info.get("education", "未填写"),
        work_experience=candidate_info.get("work_experience", 0),
        is_fresh=candidate_info.get("is_fresh", "未填写"),
        skills=candidate_info.get("skills", "未填写"),
    )
    try:
        return await _call_llm(prompt)
    except RuntimeError as e:
        print(f"[WARN] question_generator: AI 备注生成失败（模型调用错误 - {e}），使用 fallback 数据")
        return "AI备注生成失败"
    except Exception as e:
        print(f"[WARN] question_generator: AI 备注生成失败（未知错误 - {e}），使用 fallback 数据")
        return "AI备注生成失败"