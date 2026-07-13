"""语调分析 + 语音转写模块 (Qwen3-Omni-Flash via OpenAI-compatible API)

一次 API 调用同时完成：
1. 语音转写为文字
2. 语调情感分析（自信度、情绪、语速）
"""
import os
import json
import base64
from openai import OpenAI
from config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, OMNI_MODEL

# 全局 OpenAI 客户端（单例）
_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url=DASHSCOPE_BASE_URL,
        )
    return _client


def analyze_tone(audio_path: str) -> dict:
    """使用 Qwen3-Omni-Flash 分析语音，返回转写文本与语调特征

    Args:
        audio_path: 本地音频文件的绝对路径

    Returns:
        dict: {
            "transcript":   "语音转写文字",
            "emotion_hint": "总体感觉（自信有活力/平稳自然/较为平淡）",
            "confidence":   "自信/一般/不自信",
            "emotion":      "积极/中性/消极",
            "speed":        "快/正常/慢",
            "error":        "失败时的错误信息（可选）"
        }
    """
    # ── 检查配置 ──
    if not DASHSCOPE_API_KEY or DASHSCOPE_API_KEY.startswith("your-"):
        print("[WARN] tone_analyzer: API Key 未配置，使用 fallback 数据")
        return {
            "transcript": "[语音服务未配置，返回占位转写文本。候选人详细回答了项目经验和技术能力。]",
            "emotion_hint": "服务未配置",
            "confidence": "未知",
            "emotion": "未知",
            "speed": "未知",
        }

    if not os.path.isfile(audio_path):
        return {
            "transcript": f"[文件不存在: {audio_path}]",
            "emotion_hint": "分析失败",
            "error": "文件不存在",
        }

    # ── 读取并 Base64 编码音频 ──
    try:
        with open(audio_path, "rb") as f:
            audio_data = f.read()
    except Exception as e:
        return {
            "transcript": f"[读取音频文件失败: {e}]",
            "emotion_hint": "分析失败",
            "error": str(e),
        }

    base64_audio = base64.b64encode(audio_data).decode("utf-8")
    if len(base64_audio) > 10 * 1024 * 1024:
        return {
            "transcript": "[音频文件超过 Base64 10MB 限制，无法分析]",
            "emotion_hint": "分析失败",
            "error": "Base64 编码后超过 10MB",
        }

    # ── 确定音频格式 ──
    ext = os.path.splitext(audio_path)[1].lower().lstrip(".")
    if ext not in ("mp3", "wav", "m4a", "aac", "amr", "3gp", "3gpp"):
        ext = "wav"

    # ── 调用 Qwen3-Omni-Flash ──
    try:
        client = _get_client()
        completion = client.chat.completions.create(
            model=OMNI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": f"data:;base64,{base64_audio}",
                                "format": ext,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "请完成两项任务：\n"
                                "1. 将这段语音完整转写为文字\n"
                                "2. 分析说话者的语调特征\n\n"
                                "严格按以下JSON格式返回，不要包含其他内容：\n"
                                '{\n'
                                '  "transcript": "语音转写文字",\n'
                                '  "emotion_hint": "总体感觉，例如：自信有活力/平稳自然/较为平淡",\n'
                                '  "confidence": "自信/一般/不自信",\n'
                                '  "emotion": "积极/中性/消极",\n'
                                '  "speed": "快/正常/慢"\n'
                                '}'
                            ),
                        },
                    ],
                },
            ],
            modalities=["text"],
            stream=True,  # Qwen3-Omni-Flash 必须使用流式输出
            stream_options={"include_usage": True},
        )

        # 收集流式响应
        full_content = ""
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content:
                full_content += chunk.choices[0].delta.content

        if not full_content:
            return {
                "transcript": "[模型返回为空]",
                "emotion_hint": "分析失败",
            }

        # 解析 JSON
        try:
            result = json.loads(full_content)
            print(result)
            return {
                "transcript": result.get("transcript", full_content),
                "emotion_hint": result.get("emotion_hint", "未知"),
                "confidence": result.get("confidence", "未知"),
                "emotion": result.get("emotion", "未知"),
                "speed": result.get("speed", "未知"),
            }
        except json.JSONDecodeError:
            return {
                "transcript": full_content,
                "emotion_hint": "平稳自然",
                "confidence": "未知",
                "emotion": "未知",
                "speed": "未知",
                "note": "模型未按 JSON 格式返回，此为原始输出",
            }

    except Exception as e:
        print(f"[WARN] tone_analyzer: 分析失败，使用 fallback 数据 - {e}")
        return {
            "transcript": f"[语音分析失败: {e}]",
            "emotion_hint": "分析失败",
            "error": str(e),
        }