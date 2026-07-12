# AI面试官与人才评估系统 — 后端API接口文档

> **版本**: V1.0 | **Base URL**: `http://{host}:8000/api` | **格式**: JSON | **认证**: JWT (Bearer Token)

---

## 目录

1. [通用规范](#1-通用规范)
2. [认证模块](#2-认证模块-auth)
3. [岗位管理模块](#3-岗位管理模块-jobs)
4. [候选人管理模块](#4-候选人管理模块-candidates)
5. [面试管理模块](#5-面试管理模块-interviews)
6. [面试报告模块](#6-面试报告模块-reports)
7. [通讯模块](#7-通讯模块-messages)
8. [错误码参考](#8-错误码参考)

---

## 1. 通用规范

### 1.1 请求头

```
Content-Type: application/json
Authorization: Bearer {access_token}   (除 /auth/* 外必填)
```

### 1.2 分页参数

```
GET /api/resource?page=1&size=20
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 (从1开始) |
| size | int | 20 | 每页数量 (最大100) |

分页响应格式：

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

### 1.3 统一响应格式

成功：
```json
{ "code": 200, "data": {...}, "message": "ok" }
```

失败：
```json
{ "code": 4xx, "data": null, "message": "错误描述" }
```

### 1.4 HTTP 状态码约定

| 状态码 | 含义 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 / Token 过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 业务冲突 (如重复报名) |
| 422 | 请求体验证失败 |
| 500 | 服务器内部错误 |

---

## 2. 认证模块 `/auth`

### 2.1 面试者注册

```
POST /auth/register
```

**请求体**：
```json
{
  "name": "张三",
  "password": "abc123456"
}
```

**响应** `201`：
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

**校验规则**：
- `name`: 必填，2-20 字符
- `password`: 必填，6-50 字符
- 账号为系统自动生成的 6 位不重复数字

### 2.2 登录 (面试官 & 面试者通用)

```
POST /auth/login
```

**请求体**：
```json
{
  "account": "384729",
  "password": "abc123456"
}
```

**响应** `200`：
```json
{
  "code": 200,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "account": "384729",
      "name": "张三",
      "role": "interviewee"
    }
  },
  "message": "ok"
}
```

**说明**：面试官账号由系统预创建，不可通过注册接口创建。

### 2.3 获取当前用户信息

```
GET /auth/me
```

**响应** `200`：
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "account": "384729",
    "name": "张三",
    "role": "interviewee",
    "education": "本科",
    "work_experience": 3,
    "is_fresh": "往届",
    "salary_expectation": "15K-20K",
    "skills": "Python, FastAPI, Vue.js",
    "experience": "3年后端开发经验...",
    "avatar_url": "/uploads/avatars/384729.jpg"
  },
  "message": "ok"
}
```

---

## 3. 岗位管理模块 `/jobs`

### 3.1 创建岗位 (面试官)

```
POST /jobs
```

**请求体**：
```json
{
  "title": "后端开发工程师",
  "salary_range": "15K-25K",
  "education_requirement": "本科",
  "work_experience_requirement": 3,
  "fresh_requirement": "往届",
  "work_content": "负责后端API开发与维护...",
  "position_requirements": "良好的团队协作能力..."
}
```

**响应** `201`：返回完整岗位对象 (含 `id`, `created_by`, `created_at`)。

**权限**：仅面试官。

### 3.2 查询岗位列表

```
GET /jobs?page=1&size=20&sort=salary_range&order=desc&education_requirement=本科
```

| 查询参数 | 类型 | 说明 |
|----------|------|------|
| title | string | 按职位名模糊搜索 |
| education_requirement | string | 按学历筛选 |
| work_experience_requirement | int | 按经验年限筛选 (>=此值) |
| fresh_requirement | enum | `应届` / `往届` / `不限` |
| sort | string | 排序字段: `title`, `salary_range`, `work_experience_requirement`, `created_at` |
| order | string | `asc` / `desc`，默认 `desc` |

**响应** `200`：分页岗位列表。

**权限**：面试官和面试者均可访问。

### 3.3 查询岗位详情

```
GET /jobs/{job_id}
```

**响应** `200`：完整岗位对象。

**说明**：面试者查看时，额外返回 `has_applied` (bool) 字段表示是否已报名。

### 3.4 更新岗位 (面试官)

```
PUT /jobs/{job_id}
```

**请求体**：同 3.1，所有字段可选。

**权限**：仅面试官，且仅限创建者本人。

### 3.5 删除岗位 (面试官)

```
DELETE /jobs/{job_id}
```

**响应** `200`。

**权限**：仅面试官，且仅限创建者本人。若已有面试者报名则返回 `409`。

### 3.6 意向面试者仓库

#### 3.6.1 查看意向面试者列表

```
GET /jobs/{job_id}/applicants?page=1&size=20
```

**响应** `200`：
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "interviewee_id": 5,
        "name": "张三",
        "education": "本科",
        "work_experience": 3,
        "is_fresh": "往届",
        "skills": "Python, FastAPI",
        "ai_note": "匹配:工作经验满足要求",
        "applied_at": "2026-07-10T14:30:00"
      }
    ],
    "total": 12,
    "page": 1,
    "size": 20
  },
  "message": "ok"
}
```

**权限**：仅面试官 (创建者)。

**说明**：`ai_note` 字段为 AI 自动对比岗位要求与面试者信息后生成的格式化备注。

#### 3.6.2 创建通讯渠道 (从意向仓库)

```
POST /jobs/{job_id}/applicants/{interviewee_id}/message-channel
```

**响应** `201`：
```json
{
  "code": 201,
  "data": { "channel_id": 42 },
  "message": "通讯渠道已创建"
}
```

**说明**：若渠道已存在则返回已有 `channel_id` (不重复创建)。

---

## 4. 候选人管理模块 `/candidates`

> 候选人与面试者为同一实体。本模块供面试官查看面试者的公开信息。

### 4.1 面试者个人信息编辑 (面试者)

```
PUT /auth/me/profile
```

**请求体**：
```json
{
  "education": "本科",
  "work_experience": 3,
  "is_fresh": "往届",
  "salary_expectation": "15K-20K",
  "skills": "Python, FastAPI, Vue.js, MySQL",
  "experience": "3年后端开发经验，主导过..."
}
```

**权限**：仅面试者。

### 4.2 上传头像 (面试者)

```
POST /auth/me/avatar
Content-Type: multipart/form-data
```

| 表单字段 | 类型 | 说明 |
|----------|------|------|
| avatar | file | 图片文件 (jpg/png, <=2MB) |

**响应** `200`：
```json
{ "code": 200, "data": { "avatar_url": "/uploads/avatars/384729.jpg" } }
```

---

## 5. 面试管理模块 `/interviews`

### 5.1 创建面试 (面试官)

```
POST /interviews
```

**请求体**：
```json
{
  "job_id": 3,
  "interviewee_id": 5
}
```

**响应** `201`：
```json
{
  "code": 201,
  "data": {
    "id": 17,
    "job": { "id": 3, "title": "后端开发工程师" },
    "interviewee": { "id": 5, "name": "张三" },
    "status": "未定时",
    "questions": [
      {
        "id": 101,
        "question_text": "请描述你在项目中...",
        "question_type": "技术",
        "sort_order": 1
      }
    ],
    "open_time_start": null,
    "open_time_end": null
  },
  "message": "面试创建成功，AI已生成5道问题"
}
```

**后端处理流程**：
1. 查询岗位 JD + 面试者个人信息
2. 调用 AI 模块生成 5 道问题 (技术/行为/情景)
3. 保存面试记录 + 问题
4. 返回完整面试对象

### 5.2 查询面试列表

```
GET /interviews?status=未开始&page=1&size=20&sort=created_at&order=desc
```

| 查询参数 | 类型 | 说明 |
|----------|------|------|
| status | enum | `未定时` / `未开始` / `正在进行` / `已结束` |
| job_id | int | 按岗位筛选 |
| sort | string | `created_at`, `open_time_start`, `status` |

**面试官视角**：返回自己创建的所有面试。  
**面试者视角**：返回自己被关联且面试官已确定开放时间的面试 (不显示 `未定时` 状态的面试)。

### 5.3 查询面试详情

```
GET /interviews/{interview_id}
```

**响应** `200`：完整面试对象，含 5 道问题、面试者信息、岗位信息。

### 5.4 设置 / 修改面试开放时间

```
PUT /interviews/{interview_id}/open-time
```

**请求体**：
```json
{
  "open_time_start": "2026-07-15T09:00:00",
  "open_time_end": "2026-07-15T18:00:00"
}
```

**状态变更**：`未定时` → `未开始` (首次设置)。  
**权限**：仅面试官，仅限创建者。

### 5.5 修改面试问题 (面试官)

```
PUT /interviews/{interview_id}/questions/{question_id}
```

**请求体**：
```json
{ "question_text": "修改后的题目文本..." }
```

**权限**：仅面试官，仅限创建者，且仅在 `未定时` 或 `未开始` 状态可修改。

### 5.6 进入面试校验 (面试者)

```
GET /interviews/{interview_id}/check-in
```

**响应** `200` (准入)：
```json
{
  "code": 200,
  "data": {
    "current_question": {
      "id": 101,
      "question_text": "请描述你在项目中...",
      "total_questions": 5,
      "current_index": 1
    }
  },
  "message": "可以进入面试"
}
```

**响应** `403` (拒绝)：
```json
{ "code": 403, "message": "面试尚未开放 / 面试已结束 / 您已完成所有题目" }
```

**校验规则**：
- 当前时间必须在 `[open_time_start, open_time_end]` 内
- 面试状态必须为 `正在进行`
- 面试者尚未完成全部 5 题

### 5.7 提交语音回答 (面试者)

```
POST /interviews/{interview_id}/answers
Content-Type: multipart/form-data
```

| 表单字段 | 类型 | 说明 |
|----------|------|------|
| audio_file | file | 语音录音文件 (wav/mp3/m4a, <=10MB) |
| question_id | int | 对应的问题ID |

**响应** `201`：
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

若为第 5 题回答，则 `next_question` 为 `null`，面试状态自动变更为 `已结束`。

### 5.8 查询回答状态

```
GET /interviews/{interview_id}/answers
```

**响应** `200`：
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 55,
        "question_id": 101,
        "question_text": "请描述...",
        "transcript": "我在上一个项目中...",
        "content_analysis": "回答完整，逻辑清晰...",
        "answered_at": "2026-07-15T09:15:00"
      }
    ],
    "completed_count": 5,
    "total_count": 5,
    "all_completed": true
  },
  "message": "ok"
}
```

**说明**：若 AI 尚未完成语音分析，`transcript` 和 `content_analysis` 字段为 `null`。

### 5.9 创建通讯渠道 (从面试)

```
POST /interviews/{interview_id}/message-channel
```

**响应** `201`：`{ "channel_id": 42 }`。若已存在则返回已有 ID。

---

## 6. 面试报告模块 `/reports`

### 6.1 生成面试报告 (面试官)

```
POST /interviews/{interview_id}/report/generate
```

**权限**：仅面试官，仅限创建者。面试状态必须为 `已结束` 且尚未生成报告。

**后端处理流程**：
1. 收集 5 道题的转写文本 + 语调特征
2. 调用 AI 评估模块
3. 生成四维度评分 + 摘要 + 亮点 + 风险
4. 拼装结构化报告 → 存入 report 表

**响应** `201`：
```json
{
  "code": 201,
  "data": {
    "id": 8,
    "interview_id": 17,
    "interviewee_name": "张三",
    "job_title": "后端开发工程师",
    "answer_summary": "候选人在5道题的回答中...",
    "highlights": "1. 技术功底扎实...\n2. 沟通表达清晰...",
    "risks": "1. 在某些领域经验不足...",
    "recommendation": "推荐录用，候选人完全胜任岗位要求",
    "skill_score": 85,
    "communication_score": 78,
    "logic_score": 82,
    "culture_score": 88,
    "interviewer_rating": null,
    "generated_at": "2026-07-15T10:30:00"
  },
  "message": "报告生成成功"
}
```

### 6.2 查询报告列表

```
GET /reports?page=1&size=20&sort=generated_at&order=desc&job_id=3&rating=A
```

| 查询参数 | 类型 | 说明 |
|----------|------|------|
| job_id | int | 按岗位筛选 |
| rating | enum | 按评级筛选: `S` / `A` / `B` / `C` |
| interviewee_name | string | 按面试者姓名模糊搜索 |
| sort | string | `generated_at`, `skill_score`, `communication_score`, `logic_score`, `culture_score`, `rating` |

### 6.3 查询报告详情

```
GET /reports/{report_id}
```

**响应** `200`：完整报告对象。

### 6.4 对报告评级 (面试官)

```
PUT /reports/{report_id}/rating
```

**请求体**：
```json
{ "rating": "A" }
```

**校验**：`rating` 必须为 `S` / `A` / `B` / `C` 之一。

### 6.5 下载报告 PDF

```
GET /reports/{report_id}/download
```

**响应** `200`：返回 PDF 文件流 (`Content-Type: application/pdf`)。

**说明**：首次下载时后端使用 Jinja2 模板渲染生成 PDF；再次请求直接返回已生成的文件。

### 6.6 创建通讯渠道 (从报告)

```
POST /reports/{report_id}/message-channel
```

**响应** `201`：`{ "channel_id": 42 }`。若已存在则返回已有 ID。

---

## 7. 通讯模块 `/messages`

### 7.1 查询通讯渠道列表

```
GET /messages/channels?page=1&size=20
```

**响应** `200` (面试官视角)：
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 42,
        "interviewee": { "id": 5, "name": "张三", "account": "384729" },
        "created_from": "意向仓库",
        "last_message": { "content": "面试时间已更新", "sent_at": "2026-07-10T16:00:00" },
        "created_at": "2026-07-10T14:30:00"
      }
    ],
    "total": 3
  },
  "message": "ok"
}
```

### 7.2 查询渠道内的消息

```
GET /messages/channels/{channel_id}?page=1&size=50
```

**响应** `200`：按时间升序排列的消息列表。

### 7.3 发送消息

```
POST /messages/channels/{channel_id}
```

**请求体**：
```json
{ "content": "您好，您的面试时间为7月15日上午9点" }
```

**校验**：`content` 必填，1-2000 字符。

**响应** `201`：
```json
{
  "code": 201,
  "data": {
    "id": 256,
    "sender_type": "面试官",
    "content": "您好，您的面试时间为7月15日上午9点",
    "sent_at": "2026-07-14T10:00:00"
  },
  "message": "发送成功"
}
```

**权限规则**：
- 面试官：可向自己创建的渠道发消息
- 面试者：仅可在面试官已创建渠道后回复 (不能主动创建渠道)

---

## 8. 错误码参考

| 业务码 | 含义 | 触发场景 |
|--------|------|----------|
| 1001 | 账号不存在 | 登录时账号未找到 |
| 1002 | 密码错误 | 登录时密码不匹配 |
| 1003 | 账号已存在 | 注册时系统生成的账号冲突 (极罕见) |
| 2001 | 已报名该岗位 | 面试者重复报名同一岗位 |
| 2002 | 岗位存在报名者 | 面试官尝试删除已有报名者的岗位 |
| 3001 | 面试状态不允许此操作 | 如在非"未定时"状态修改问题 |
| 3002 | 面试未开放 | 面试者在非开放时间尝试进入 |
| 3003 | 面试已结束 | 面试者已完成全部5题后再次进入 |
| 3004 | 已生成报告 | 面试官对已有报告的面试再次生成 |
| 4001 | 报告不存在 | 查询或操作不存在的报告 |
| 5001 | 通讯渠道不存在 | 操作不存在的通讯渠道 |
| 5002 | 无权限操作该渠道 | 面试者操作不属于自己的渠道 |
| 6001 | AI服务超时 | 调用AI模块超时 (30秒) |
| 6002 | AI服务异常 | 调用AI模块返回错误 |
| 9999 | 服务器内部错误 | 未预期的运行时错误 |

---

> **文档维护**: 本文档随 API 版本同步更新。接口发生变更时，同步修改版本号和对应条目。
