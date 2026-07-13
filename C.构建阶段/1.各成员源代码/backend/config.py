"""应用配置"""
import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv()

# ═══════════════════════════════════════════
# 数据库
# ═══════════════════════════════════════════
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_NAME = os.getenv("DB_NAME", "ai_interview")
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# ═══════════════════════════════════════════
# JWT
# ═══════════════════════════════════════════
SECRET_KEY = os.getenv("SECRET_KEY", "ai-interview-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 86400  # 24h

# ═══════════════════════════════════════════
# 文件上传
# ═══════════════════════════════════════════
UPLOAD_DIR = BASE_DIR / "uploads"
AVATAR_DIR = UPLOAD_DIR / "avatars"
AUDIO_DIR = UPLOAD_DIR / "audios"
REPORT_DIR = UPLOAD_DIR / "reports"
MAX_AVATAR_SIZE = 2 * 1024 * 1024
MAX_AUDIO_SIZE = 10 * 1024 * 1024

# ═══════════════════════════════════════════
# DashScope — Omni 多模态专用（始终走千问，不切换）
# ═══════════════════════════════════════════
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL",
                                "https://ws-83p69eaoba9g00a6.cn-beijing.maas.aliyuncs.com/compatible-mode/v1")
OMNI_MODEL = os.getenv("OMNI_MODEL", "qwen3-omni-flash")

# ═══════════════════════════════════════════
# LLM — 文本模型
# ═══════════════════════════════════════════
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-3.6plus")

# ═══════════════════════════════════════════
# 分页
# ═══════════════════════════════════════════
DEFAULT_PAGE = 1
DEFAULT_SIZE = 20
MAX_SIZE = 100