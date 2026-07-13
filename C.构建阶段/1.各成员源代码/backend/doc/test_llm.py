"""LLM 模型调用诊断工具

依次测试：
1. 配置检查（API Key、URL、模型名）
2. 简单对话测试
3. 面试出题 prompt 测试
4. 报告评估 prompt 测试
5. 返回格式解析验证
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from ai.prompts import QUESTION_GENERATION_PROMPT, REPORT_ASSESSMENT_PROMPT


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_config():
    """检查配置"""
    separator("1️⃣  配置检查")
    print(f"  LLM_API_KEY:     {'✅ 已配置 (' + LLM_API_KEY[:20] + '...)' if LLM_API_KEY and not LLM_API_KEY.startswith('your-') else '❌ 未配置'}")
    print(f"  LLM_BASE_URL:    {LLM_BASE_URL}")
    print(f"  LLM_MODEL:       {LLM_MODEL}")
    print(f"  模型名:          {LLM_MODEL}")


def _get_client() -> OpenAI:
    return OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)


def test_simple_chat():
    """简单对话测试"""
    separator("2️⃣  简单对话测试")
    print("  发送: '你好'")
    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": "你好"}],
        )
        content = resp.choices[0].message.content or ""
        print(f"  ✅ 返回内容: {content[:100]}")
        return True
    except Exception as e:
        print(f"  ❌ 异常: {type(e).__name__}: {e}")
        return False


def test_question_prompt():
    """面试出题 prompt 测试"""
    separator("3️⃣  面试出题 prompt 测试")
    prompt = QUESTION_GENERATION_PROMPT.format(
        job_title="后端开发工程师",
        education="本科",
        work_exp=3,
        work_content="负责后端 API 开发与维护",
        position_req="熟悉 Python / FastAPI",
        name="张三",
        candidate_edu="本科",
        candidate_exp=3,
        skills="Python, FastAPI, MySQL",
        experience="3年后端开发经验",
    )
    print(f"  Prompt 长度: {len(prompt)} 字符")
    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = resp.choices[0].message.content or ""
        print(f"  原始响应长度: {len(content)} 字符")
        print(f"\n  📤 原始响应（前300字符）:\n{content[:300]}\n")
        return content
    except Exception as e:
        print(f"  ❌ 异常: {type(e).__name__}: {e}")
        return None


def test_report_prompt():
    """报告评估 prompt 测试"""
    separator("4️⃣  报告评估 prompt 测试")
    prompt = REPORT_ASSESSMENT_PROMPT.format(
        interviewee_name="张三",
        job_title="后端开发工程师",
        answers_summary="题目: 请介绍项目经验\n回答: 3年开发经验\n\n题目: 技术难点\n回答: 解决高并发问题",
    )
    print(f"  Prompt 长度: {len(prompt)} 字符")
    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        content = resp.choices[0].message.content or ""
        print(f"  原始响应长度: {len(content)} 字符")
        print(f"\n  📤 原始响应（前300字符）:\n{content[:300]}\n")
        return content
    except Exception as e:
        print(f"  ❌ 异常: {type(e).__name__}: {e}")
        return None


def parse_and_validate_questions(raw: str) -> bool:
    """验证出题返回格式"""
    separator("5️⃣  返回格式验证 - 面试出题")
    if raw is None:
        print("  ⏭️  跳过（上一步无返回）")
        return False

    # 检查是否包含 Markdown 代码块
    import re
    code_block = re.search(r"```(?:json)?\s*\n?(.*?)```", raw, re.DOTALL)
    extract = code_block.group(1).strip() if code_block else raw

    start = extract.find("[")
    end = extract.rfind("]") + 1

    if start < 0 or end <= start:
        print("  ❌ 未找到 JSON 数组 '[' / ']'")
        print(f"  💡 修复建议: 在 prompt 中强调 '只返回JSON，不要加markdown代码块'")
        return False

    try:
        questions = json.loads(extract[start:end])
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON 解析失败: {e}")
        return False

    print(f"  ✅ 解析成功，题目数: {len(questions)}")
    for i, q in enumerate(questions, 1):
        q_text = q.get("question_text", "?")
        q_type = q.get("question_type", "?")
        print(f"     [{i}] ({q_type}) {q_text[:60]}...")

    if len(questions) == 5:
        print(f"  ✅ 题目数=5，符合要求")
        return True
    else:
        print(f"  ❌ 题目数={len(questions)}，期望5道")
        return False


def parse_and_validate_report(raw: str) -> bool:
    """验证报告返回格式"""
    separator("6️⃣  返回格式验证 - 报告评估")
    if raw is None:
        print("  ⏭️  跳过（上一步无返回）")
        return False

    import re
    code_block = re.search(r"```(?:json)?\s*\n?(.*?)```", raw, re.DOTALL)
    extract = code_block.group(1).strip() if code_block else raw

    start = extract.find("{")
    end = extract.rfind("}") + 1

    if start < 0 or end <= start:
        print("  ❌ 未找到 JSON 对象 '{' / '}'")
        return False

    try:
        report = json.loads(extract[start:end])
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON 解析失败: {e}")
        return False

    print(f"  ✅ JSON 解析成功")
    required_keys = ["answer_summary", "skill_score", "communication_score", "logic_score", "culture_score"]
    missing = [k for k in required_keys if k not in report]
    if missing:
        print(f"  ⚠️  缺少字段: {missing}")
    else:
        print(f"  ✅ 包含所有必需字段")
        print(f"     评分: 技能={report['skill_score']} 沟通={report['communication_score']} 逻辑={report['logic_score']} 文化={report['culture_score']}")
    return len(missing) == 0


def summary(results: list):
    """汇总"""
    separator("📊  诊断汇总")
    passed = sum(1 for r in results if r)
    total = len(results)
    for i, r in enumerate(results, 1):
        status = "✅" if r else "❌"
        name = ["简单对话", "出题调用", "报告调用", "出题格式", "报告格式"][i - 1]
        print(f"  {status} 测试{i}: {name}")
    print(f"\n  {passed}/{total} 项通过")


def main():
    print("\n🔍  AI 模型诊断工具")
    print(f"  Python: {sys.version.split()[0]}")

    check_config()

    # 前置条件
    if not LLM_API_KEY or LLM_API_KEY.startswith("your-"):
        print("\n⚠️  API Key 未配置，无法继续测试")
        print("   请设置 .env 中的 LLM_API_KEY")
        return

    # 执行测试
    simple_ok = test_simple_chat()

    q_raw = test_question_prompt() if simple_ok else None
    r_raw = test_report_prompt() if simple_ok else None

    q_format_ok = parse_and_validate_questions(q_raw)
    r_format_ok = parse_and_validate_report(r_raw)

    summary([simple_ok, q_raw is not None, r_raw is not None, q_format_ok, r_format_ok])


if __name__ == "__main__":
    main()
