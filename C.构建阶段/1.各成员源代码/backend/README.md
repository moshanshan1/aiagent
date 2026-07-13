# AI面试官与人才评估系统 - 后端

## 技术栈

- **框架**: FastAPI (Python)
- **数据库**: MySQL (PyMySQL + SQLAlchemy ORM)
- **认证**: JWT (python-jose + passlib/bcrypt)
- **AI**: DeepSeek (文本分析)、Qwen-Audio (语音识别)、librosa (语调分析)
- **文件处理**: python-multipart, weasyprint (PDF生成)

## 项目结构

```
backend/
├── main.py                 # FastAPI 应用入口
├── config.py               # 配置 (数据库/JWT/AI)
├── database.py             # 数据库连接
├── init_db.py              # 数据库初始化脚本
├── requirements.txt        # Python 依赖
├── .env                    # 环境变量
├── models/                 # SQLAlchemy 数据模型
│   ├── user.py             # 用户
│   ├── job.py              # 岗位 + 报名
│   ├── interview.py        # 面试 + 问题 + 回答
│   ├── report.py           # 面试报告
│   └── message.py          # 通讯渠道 + 消息
├── schemas/                # Pydantic 请求/响应模型
│   ├── auth.py
│   ├── job.py
│   ├── interview.py
│   ├── report.py
│   └── message.py
├── routers/                # API 路由
│   ├── auth.py             # /api/auth/*
│   ├── jobs.py             # /api/jobs/*
│   ├── interviews.py       # /api/interviews/*
│   ├── reports.py          # /api/reports/*
│   └── messages.py         # /api/messages/*
├── services/               # 业务逻辑层
│   ├── auth_service.py
│   ├── job_service.py
│   ├── interview_service.py
│   ├── report_service.py
│   └── message_service.py
├── ai/                     # AI 核心模块
│   ├── prompts.py          # Prompt 模板库
│   ├── question_generator.py  # 问题生成 (DeepSeek)
│   ├── asr.py              # 语音转写 (Qwen-Audio)
│   ├── tone_analyzer.py    # 语调分析 (librosa)
│   └── assessor.py         # 四维度评估 + 报告 (DeepSeek)
├── utils/                  # 工具模块
│   ├── security.py         # JWT + 密码哈希
│   ├── file_storage.py     # 文件上传存储
│   └── account_generator.py # 6位账号生成
└── uploads/                # 上传文件目录
    ├── avatars/            # 头像
    ├── audios/             # 录音
    └── reports/            # 报告PDF
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

确保 MySQL 已安装并运行，创建数据库：

```sql
CREATE DATABASE ai_interview CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

修改 `.env` 文件中的数据库连接信息：

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=ai_interview
```

### 3. 配置 AI 服务 (可选)

在 `.env` 中填入 API Key：

```
DEEPSEEK_API_KEY=sk-xxx
QWEN_API_KEY=sk-xxx
```

> 未配置 AI Key 时，系统会使用内置的 fallback 数据正常运行。

### 4. 初始化数据库

```bash
python init_db.py
```

### 5. 启动服务

```bash
python main.py
```

服务启动后访问 http://localhost:8000/docs 查看 Swagger 文档。

## 默认账号

| 角色   | 账号   | 密码      |
|--------|--------|-----------|
| 面试官 | 000001 | admin123  |
| 面试官 | 000002 | admin123  |
| 面试者 | 注册获取 | 自行设置 |

## API 概览

| 模块     | 路径前缀           | 说明                     |
|----------|--------------------|--------------------------|
| 认证     | `/api/auth`        | 注册、登录、个人信息     |
| 岗位     | `/api/jobs`        | 岗位 CRUD、报名、意向仓库 |
| 面试     | `/api/interviews`  | 创建面试、签到、语音答题 |
| 报告     | `/api/reports`     | 生成报告、评级、下载PDF  |
| 通讯     | `/api/messages`    | 通讯渠道、消息收发       |

详细接口文档请参考 `API接口文档.md` 或启动后访问 Swagger UI。