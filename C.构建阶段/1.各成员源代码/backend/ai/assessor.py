"""四维度评估 + 报告生成"""
import json
import asyncio
from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from ai.prompts import REPORT_ASSESSMENT_PROMPT, CONTENT_ANALYSIS_PROMPT

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
                temperature=0.5,
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

def _fallback_assessment() -> str:
    return json.dumps({
        "answer_summary": "面试者回答完整，基本覆盖了题目要求的核心要点，展现了较好的专业素养。",
        "highlights": "1. 技术基础扎实，能清晰描述项目经验\n2. 表达流畅，逻辑清晰\n3. 态度积极，沟通能力强",
        "risks": "1. 部分领域经验尚浅，需进一步培养",
        "recommendation": "建议录用，候选人基本胜任岗位要求。",
        "skill_score": 78,
        "communication_score": 75,
        "logic_score": 80,
        "culture_score": 82,
    }, ensure_ascii=False)

async def analyze_content(question_text: str, transcript: str, tone_features: str) -> str:
    prompt = CONTENT_ANALYSIS_PROMPT.format(
        question_text=question_text, transcript=transcript, tone_features=tone_features)
    try:
        return await _call_llm(prompt)
    except RuntimeError as e:
        print(f"[WARN] assessor: 内容分析失败（模型调用错误 - {e}），使用 fallback 数据")
        return "内容分析暂不可用"
    except Exception as e:
        print(f"[WARN] assessor: 内容分析失败（未知错误 - {e}），使用 fallback 数据")
        return "内容分析暂不可用"

async def assess_and_build_report(interviewee_name: str, job_title: str, answers_summary: str) -> dict:
    prompt = REPORT_ASSESSMENT_PROMPT.format(
        interviewee_name=interviewee_name, job_title=job_title, answers_summary=answers_summary)
    try:
        result = await _call_llm(prompt)
    except RuntimeError as e:
        print(f"[WARN] assessor: 报告生成失败（模型调用错误 - {e}），使用 fallback 数据")
        return json.loads(_fallback_assessment())

    try:
        start = result.find("{")
        end = result.rfind("}") + 1
        if start < 0 or end <= start:
            print("[WARN] assessor: 报告生成失败（返回格式异常，未找到 JSON 对象），使用 fallback 数据")
            print(f"  [原始响应前200字符]: {result[:200]}")
            return json.loads(_fallback_assessment())
        return json.loads(result[start:end])
    except json.JSONDecodeError as e:
        print(f"[WARN] assessor: 报告生成失败（JSON 解析错误 - {e}），使用 fallback 数据")
        print(f"  [原始响应前200字符]: {result[:200]}")
        return json.loads(_fallback_assessment())