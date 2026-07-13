# AI面试官与人才评估系统 - 后端测试计划

## 一、测试前准备

### 1.1 环境启动

```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 确保 MySQL 运行中，创建数据库
# mysql -u root -p
# CREATE DATABASE ai_interview CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 3. 修改 .env 中的数据库密码

# 4. 初始化数据库（建表 + 创建默认面试官）
python init_db.py

# 5. 启动服务
python main.py
# 或: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 1.2 Postman 全局配置

在 Postman 中设置环境变量：

| 变量名 | 初始值 | 说明 |
|--------|--------|------|
| `base_url` | `http://localhost:8000/api` | API 基地址 |
| `token_interviewer` | (登录后填入) | 面试官 JWT |
| `token_interviewee` | (登录后填入) | 面试者 JWT |
| `job_id` | (创建岗位后填入) | 岗位ID |
| `interview_id` | (创建面试后填入) | 面试ID |
| `report_id` | (生成报告后填入) | 报告ID |
| `channel_id` | (创建渠道后填入) | 通讯渠道ID |

### 1.3 请求头模板

除 `/auth/register` 和 `/auth/login` 外，所有请求需携带：

```
Content-Type: application/json
Authorization: Bearer {{token_interviewer}}   (或 {{token_interviewee}})
```

---

## 二、测试用例（按业务流程顺序）

### 阶段 1：认证模块 `/auth`

#### TC-01 面试者注册

```
POST {{base_url}}/auth/register
Content-Type: application/json

{
  "name": "张三",
  "password": "abc123456"
}
```

**预期响应** (201):
```json
{
  "code": 201,
  "data": {
    "account": "384729",
    "name": "张三",
    "role": "interviewee"
  },
  "message": "注册成功，请妥善保管您的账号"
}
```

**验证点**:
- [ ] 返回 6 位数字账号
- [ ] role 为 "interviewee"
- [ ] 记录账号，后续登录使用

**边界测试**:
- name 为空 → 422
- name 只有1个字符 → 422
- password 少于6位 → 422

---

#### TC-02 面试官登录

```
POST {{base_url}}/auth/login
Content-Type: application/json

{
  "account": "000001",
  "password": "admin123"
}
```

**预期响应** (200):
```json
{
  "code": 200,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "account": "000001",
      "name": "王面试官",
      "role": "interviewer"
    }
  },
  "message": "ok"
}
```

**操作**: 将 `access_token` 值复制到环境变量 `token_interviewer`

---

#### TC-03 面试者登录

```
POST {{base_url}}/auth/login
Content-Type: application/json

{
  "account": "TC-01中注册的账号",
  "password": "abc123456"
}
```

**操作**: 将 `access_token` 值复制到环境变量 `token_interviewee`

---

#### TC-04 登录失败 - 错误密码

```
POST {{base_url}}/auth/login
{ "account": "000001", "password": "wrongpassword" }
```

**预期**: 401，`"账号不存在"` 或 `"密码错误"`

---

#### TC-05 获取当前用户信息（面试官）

```
GET {{base_url}}/auth/me
Authorization: Bearer {{token_interviewer}}
```

**预期响应**: 返回面试官完整信息

---

#### TC-06 面试者编辑个人信息

```
PUT {{base_url}}/auth/me/profile
Authorization: Bearer {{token_interviewee}}
Content-Type: application/json

{
  "education": "本科",
  "work_experience": 3,
  "is_fresh": "往届",
  "salary_expectation": "15K-20K",
  "skills": "Python, FastAPI, Vue.js, MySQL",
  "experience": "3年后端开发经验，主导过多个Web项目..."
}
```

**预期**: 200，返回更新后的完整个人信息

---

#### TC-07 上传头像

```
POST {{base_url}}/auth/me/avatar
Authorization: Bearer {{token_interviewee}}
Content-Type: multipart/form-data

avatar: (选择一个 jpg/png 文件, < 2MB)
```

**预期**: 200，返回 `avatar_url`

---

### 阶段 2：岗位管理 `/jobs`（面试官操作）

#### TC-08 创建岗位

```
POST {{base_url}}/jobs
Authorization: Bearer {{token_interviewer}}
Content-Type: application/json

{
  "title": "后端开发工程师",
  "salary_range": "15K-25K",
  "education_requirement": "本科",
  "work_experience_requirement": 3,
  "fresh_requirement": "往届",
  "work_content": "负责后端API开发与维护，参与系统架构设计",
  "position_requirements": "良好的团队协作能力，熟悉Python和FastAPI"
}
```

**预期响应** (201): 返回完整岗位对象，含 `id`

**操作**: 将返回的 `id` 存入环境变量 `job_id`

---

#### TC-09 再创建一个岗位（用于筛选测试）

```
POST {{base_url}}/jobs
Authorization: Bearer {{token_interviewer}}

{
  "title": "前端开发工程师",
  "salary_range": "12K-20K",
  "education_requirement": "大专",
  "work_experience_requirement": 1,
  "fresh_requirement": "不限",
  "work_content": "负责Vue.js前端开发",
  "position_requirements": "熟悉Vue3和TypeScript"
}
```

---

#### TC-10 查询岗位列表

```
GET {{base_url}}/jobs?page=1&size=20
Authorization: Bearer {{token_interviewer}}
```

**预期**: 返回分页列表，包含刚才创建的2个岗位

---

#### TC-11 岗位筛选 - 按标题模糊搜索

```
GET {{base_url}}/jobs?title=后端
Authorization: Bearer {{token_interviewer}}
```

**预期**: 只返回"后端开发工程师"

---

#### TC-12 岗位筛选 - 按学历筛选

```
GET {{base_url}}/jobs?education_requirement=本科
Authorization: Bearer {{token_interviewer}}
```

---

#### TC-13 岗位排序

```
GET {{base_url}}/jobs?sort=work_experience_requirement&order=asc
Authorization: Bearer {{token_interviewer}}
```

---

#### TC-14 查询岗位详情

```
GET {{base_url}}/jobs/{{job_id}}
Authorization: Bearer {{token_interviewer}}
```

---

#### TC-15 更新岗位

```
PUT {{base_url}}/jobs/{{job_id}}
Authorization: Bearer {{token_interviewer}}
Content-Type: application/json

{
  "salary_range": "18K-28K"
}
```

**预期**: 只有 `salary_range` 被更新，其他字段不变

---

### 阶段 3：面试者报名岗位

#### TC-16 面试者查看岗位列表

```
GET {{base_url}}/jobs?page=1&size=20
Authorization: Bearer {{token_interviewee}}
```

**预期**: 每个岗位对象中包含 `has_applied: false`

---

#### TC-17 面试者报名岗位

```
POST {{base_url}}/jobs/{{job_id}}/apply
Authorization: Bearer {{token_interviewee}}
```

**预期响应** (201):
```json
{ "code": 201, "data": { "id": 1 }, "message": "报名成功" }
```

---

#### TC-18 重复报名

```
POST {{base_url}}/jobs/{{job_id}}/apply
Authorization: Bearer {{token_interviewee}}
```

**预期**: 409，`"已报名该岗位"`

---

#### TC-19 面试官查看意向面试者仓库

```
GET {{base_url}}/jobs/{{job_id}}/applicants?page=1&size=20
Authorization: Bearer {{token_interviewer}}
```

**预期**: 返回面试者列表，含 `ai_note` 字段（AI自动生成的匹配备注）

---

### 阶段 4：面试管理 `/interviews`

#### TC-20 面试官创建面试

```
POST {{base_url}}/interviews
Authorization: Bearer {{token_interviewer}}
Content-Type: application/json

{
  "job_id": {{job_id}},
  "interviewee_id": (TC-01中注册用户的id，可从意向仓库中获取)
}
```

**预期响应** (201):
```json
{
  "code": 201,
  "data": {
    "id": 17,
    "job": { "id": 3, "title": "后端开发工程师" },
    "interviewee": { "id": 5, "name": "张三" },
    "status": "未定时",
    "questions": [
      { "id": 101, "question_text": "...", "question_type": "技术", "sort_order": 1 },
      ... (共5道)
    ],
    "open_time_start": null,
    "open_time_end": null
  },
  "message": "面试创建成功，AI已生成5道问题"
}
```

**操作**: 将 `id` 存入 `interview_id`，记录5个问题的 `id`

---

#### TC-21 面试者查看面试列表

```
GET {{base_url}}/interviews
Authorization: Bearer {{token_interviewee}}
```

**预期**: 此时应为空（"未定时"状态对面试者不可见）

---

#### TC-22 面试官设置面试时间

```
PUT {{base_url}}/interviews/{{interview_id}}/open-time
Authorization: Bearer {{token_interviewer}}
Content-Type: application/json

{
  "open_time_start": "2026-07-15T09:00:00",
  "open_time_end": "2026-07-15T18:00:00"
}
```

**预期**: 状态从 "未定时" 变为 "未开始"

---

#### TC-23 面试官修改面试问题

```
PUT {{base_url}}/interviews/{{interview_id}}/questions/{{question_id}}
Authorization: Bearer {{token_interviewer}}
Content-Type: application/json

{
  "question_text": "请详细描述你在上一个项目中使用的数据库优化方案"
}
```

**预期**: 问题文本已更新

---

#### TC-24 面试者查看面试列表（现在可见）

```
GET {{base_url}}/interviews
Authorization: Bearer {{token_interviewee}}
```

**预期**: 能看到该面试（状态为"未开始"）

---

#### TC-25 面试者查看面试详情

```
GET {{base_url}}/interviews/{{interview_id}}
Authorization: Bearer {{token_interviewee}}
```

**预期**: 返回完整面试信息，含5道题目

---

### 阶段 5：语音面试流程

> **注意**: 以下测试需要修改面试开放时间为当前时间范围内，才能通过签到校验。

#### TC-26 修改面试时间为当前时段

```
PUT {{base_url}}/interviews/{{interview_id}}/open-time
Authorization: Bearer {{token_interviewer}}

{
  "open_time_start": "2026-07-12T00:00:00",
  "open_time_end": "2026-12-31T23:59:59"
}
```

---

#### TC-27 面试者签到

```
GET {{base_url}}/interviews/{{interview_id}}/check-in
Authorization: Bearer {{token_interviewee}}
```

**预期响应**:
```json
{
  "code": 200,
  "data": {
    "current_question": {
      "id": 101,
      "question_text": "请介绍...",
      "total_questions": 5,
      "current_index": 1
    }
  },
  "message": "可以进入面试"
}
```

---

#### TC-28 提交第1题语音回答

```
POST {{base_url}}/interviews/{{interview_id}}/answers
Authorization: Bearer {{token_interviewee}}
Content-Type: multipart/form-data

audio_file: (选择一个 wav/mp3 文件, < 10MB)
question_id: (第1题的id)
```

**预期响应** (201):
```json
{
  "code": 201,
  "data": {
    "answer_id": 55,
    "next_question": {
      "id": 102,
      "question_text": "...",
      "current_index": 2,
      "total_questions": 5
    }
  },
  "message": "回答已保存"
}
```

> **注意**: 由于 AI 服务可能未配置，语音转写和语调分析会返回 fallback 占位数据，这是正常的。

---

#### TC-29 依次提交第2-5题回答

重复 TC-28 的操作，分别提交剩余4道题的语音文件。

**第5题提交后预期**: `next_question` 为 `null`，面试状态自动变为 "已结束"

---

#### TC-30 查询回答状态

```
GET {{base_url}}/interviews/{{interview_id}}/answers
Authorization: Bearer {{token_interviewee}}
```

**预期**:
```json
{
  "code": 200,
  "data": {
    "items": [ ... 5个回答 ... ],
    "completed_count": 5,
    "total_count": 5,
    "all_completed": true
  }
}
```

---

#### TC-31 面试结束后再次签到

```
GET {{base_url}}/interviews/{{interview_id}}/check-in
Authorization: Bearer {{token_interviewee}}
```

**预期**: 403，`"面试已结束"` 或 `"您已完成所有题目"`

---

### 阶段 6：面试报告 `/reports`

#### TC-32 生成面试报告

```
POST {{base_url}}/interviews/{{interview_id}}/report/generate
Authorization: Bearer {{token_interviewer}}
```

**预期响应** (201):
```json
{
  "code": 201,
  "data": {
    "id": 8,
    "interview_id": 17,
    "interviewee_name": "张三",
    "job_title": "后端开发工程师",
    "answer_summary": "...",
    "highlights": "...",
    "risks": "...",
    "recommendation": "...",
    "skill_score": 78,
    "communication_score": 75,
    "logic_score": 80,
    "culture_score": 82,
    "interviewer_rating": null,
    "generated_at": "..."
  },
  "message": "报告生成成功"
}
```

**操作**: 将 `id` 存入 `report_id`

---

#### TC-33 重复生成报告

```
POST {{base_url}}/interviews/{{interview_id}}/report/generate
Authorization: Bearer {{token_interviewer}}
```

**预期**: 409，`"报告已生成"`

---

#### TC-34 查询报告列表

```
GET {{base_url}}/reports?page=1&size=20
Authorization: Bearer {{token_interviewer}}
```

---

#### TC-35 查询报告详情

```
GET {{base_url}}/reports/{{report_id}}
Authorization: Bearer {{token_interviewer}}
```

---

#### TC-36 对报告评级

```
PUT {{base_url}}/reports/{{report_id}}/rating
Authorization: Bearer {{token_interviewer}}
Content-Type: application/json

{ "rating": "A" }
```

**预期**: 200，`interviewer_rating` 变为 "A"

---

#### TC-37 非法评级

```
PUT {{base_url}}/reports/{{report_id}}/rating
Authorization: Bearer {{token_interviewer}}

{ "rating": "X" }
```

**预期**: 400，`"评级必须为 S/A/B/C"`

---

#### TC-38 下载报告 PDF

```
GET {{base_url}}/reports/{{report_id}}/download
Authorization: Bearer {{token_interviewer}}
```

**预期**: 返回 PDF 文件流（或 HTML 降级文件）

---

### 阶段 7：通讯模块 `/messages`

#### TC-39 从意向仓库创建通讯渠道

```
POST {{base_url}}/jobs/{{job_id}}/applicants/{{interviewee_id}}/message-channel
Authorization: Bearer {{token_interviewer}}
```

**预期响应** (201):
```json
{ "code": 201, "data": { "channel_id": 42 }, "message": "通讯渠道已创建" }
```

**操作**: 将 `channel_id` 存入 `channel_id`

---

#### TC-40 重复创建通讯渠道

```
POST {{base_url}}/jobs/{{job_id}}/applicants/{{interviewee_id}}/message-channel
Authorization: Bearer {{token_interviewer}}
```

**预期**: 返回相同的 `channel_id`（不重复创建）

---

#### TC-41 面试官发送消息

```
POST {{base_url}}/messages/channels/{{channel_id}}
Authorization: Bearer {{token_interviewer}}
Content-Type: application/json

{ "content": "您好，您的面试时间为7月15日上午9点" }
```

**预期响应** (201):
```json
{
  "code": 201,
  "data": {
    "id": 256,
    "sender_type": "面试官",
    "content": "您好，您的面试时间为7月15日上午9点",
    "sent_at": "..."
  },
  "message": "发送成功"
}
```

---

#### TC-42 面试者查看通讯渠道列表

```
GET {{base_url}}/messages/channels
Authorization: Bearer {{token_interviewee}}
```

**预期**: 能看到面试官创建的渠道

---

#### TC-43 面试者查看渠道内消息

```
GET {{base_url}}/messages/channels/{{channel_id}}?page=1&size=50
Authorization: Bearer {{token_interviewee}}
```

**预期**: 能看到面试官发的消息

---

#### TC-44 面试者回复消息

```
POST {{base_url}}/messages/channels/{{channel_id}}
Authorization: Bearer {{token_interviewee}}
Content-Type: application/json

{ "content": "收到，我会准时参加" }
```

---

#### TC-45 面试官查看消息

```
GET {{base_url}}/messages/channels/{{channel_id}}
Authorization: Bearer {{token_interviewer}}
```

**预期**: 能看到双方所有消息，按时间升序

---

### 阶段 8：权限与安全测试

#### TC-46 无 Token 访问受保护接口

```
GET {{base_url}}/jobs
```

**预期**: 401/403

---

#### TC-47 面试者尝试创建岗位

```
POST {{base_url}}/jobs
Authorization: Bearer {{token_interviewee}}

{ "title": "测试岗位" }
```

**预期**: 403，`"仅面试官可执行此操作"`

---

#### TC-48 面试者尝试生成报告

```
POST {{base_url}}/interviews/{{interview_id}}/report/generate
Authorization: Bearer {{token_interviewee}}
```

**预期**: 403

---

#### TC-49 面试者尝试修改面试问题

```
PUT {{base_url}}/interviews/{{interview_id}}/questions/1
Authorization: Bearer {{token_interviewee}}

{ "question_text": "hack" }
```

**预期**: 403

---

#### TC-50 面试官删除岗位（有报名者时）

```
DELETE {{base_url}}/jobs/{{job_id}}
Authorization: Bearer {{token_interviewer}}
```

**预期**: 409，`"该岗位已有面试者报名，无法删除"`

---

## 三、Postman Collection 导入

可将以下 JSON 保存为 `collection.json`，在 Postman 中 Import 即可一键导入全部请求：

> 建议手动按上述步骤依次创建，更利于理解业务流程。

---

## 四、测试检查清单

### 功能完整性

| # | 模块 | 测试点 | 状态 |
|---|------|--------|------|
| 1 | 认证 | 面试者注册 + 6位账号生成 | ☐ |
| 2 | 认证 | 面试官/面试者登录 + JWT | ☐ |
| 3 | 认证 | 个人信息编辑 + 头像上传 | ☐ |
| 4 | 岗位 | CRUD + 筛选排序 | ☐ |
| 5 | 岗位 | 面试者报名 + 重复报名拦截 | ☐ |
| 6 | 岗位 | 意向仓库 + AI备注 | ☐ |
| 7 | 面试 | 创建面试 + AI出题(5道) | ☐ |
| 8 | 面试 | 设置开放时间 + 状态流转 | ☐ |
| 9 | 面试 | 签到校验 + 时间窗口 | ☐ |
| 10 | 面试 | 语音提交 + ASR转写 + 语调分析 | ☐ |
| 11 | 面试 | 5题答完自动结束 | ☐ |
| 12 | 报告 | AI生成报告 + 四维度评分 | ☐ |
| 13 | 报告 | 评级(S/A/B/C) + PDF下载 | ☐ |
| 14 | 通讯 | 创建渠道 + 收发消息 | ☐ |

### 权限控制

| # | 测试点 | 状态 |
|---|--------|------|
| 1 | 面试者不能创建岗位 | ☐ |
| 2 | 面试者不能生成报告 | ☐ |
| 3 | 面试官不能编辑个人信息 | ☐ |
| 4 | 面试官只能操作自己创建的岗位/面试 | ☐ |
| 5 | 面试者只能回答自己的面试 | ☐ |

### 异常处理

| # | 测试点 | 状态 |
|---|--------|------|
| 1 | 错误密码登录 → 401 | ☐ |
| 2 | 无效Token → 401 | ☐ |
| 3 | 不存在的资源 → 404 | ☐ |
| 4 | 重复报名 → 409 | ☐ |
| 5 | 非法评级值 → 400 | ☐ |
| 6 | 面试未开放时签到 → 403 | ☐ |