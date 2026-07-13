import asyncio
import json
import sys
from pathlib import Path

# 确保能导入项目模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai.tone_analyzer import analyze_tone


def main():
    # 替换为你的测试音频文件路径
    audio_path = r"C:\1CS\backend\uploads\audios\test.mp3"

    print("=" * 60)
    print("🎤 测试 Qwen3-Omni-Flash 语音分析")
    print("=" * 60)

    result = analyze_tone(audio_path)

    print("\n📝 转写文本:")
    print(f"  {result.get('transcript', 'N/A')}")

    print("\n🎭 语调分析:")
    print(f"  总体感觉:  {result.get('emotion_hint', 'N/A')}")
    print(f"  自信程度:  {result.get('confidence', 'N/A')}")
    print(f"  情绪状态:  {result.get('emotion', 'N/A')}")
    print(f"  语速:      {result.get('speed', 'N/A')}")

    if "error" in result:
        print(f"\n❌ 错误: {result['error']}")

    print("\n" + "=" * 60)
    print("原始返回 JSON:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("=" * 60)


if __name__ == "__main__":
    main()