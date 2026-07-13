"""Prompt 模板库"""

QUESTION_GENERATION_PROMPT = """你是一位资深的面试出题专家。请根据以下岗位信息和面试者信息，生成5道面试题目。

## 岗位信息
- 职位名称: {job_title}
- 学历要求: {education}
- 工作经验要求: {work_exp}年
- 工作内容: {work_content}
- 职位要求: {position_req}

## 面试者信息
- 姓名: {name}
- 学历: {candidate_edu}
- 工作经验: {candidate_exp}年
- 技能: {skills}
- 个人经历: {experience}

请生成5道题目，包含技术题、行为题、情景题，难度适配面试者水平。
严格按以下JSON格式返回，不要包含其他内容:
[
  {{"question_text": "题目内容", "question_type": "技术"}},
  {{"question_text": "题目内容", "question_type": "技术"}},
  {{"question_text": "题目内容", "question_type": "行为"}},
  {{"question_text": "题目内容", "question_type": "情景"}},
  {{"question_text": "题目内容", "question_type": "情景"}}
]"""

APPLICANT_AI_NOTE_PROMPT = """你是一位HR助手。请对比以下面试者信息与岗位要求，给出一句简短的格式化备注（50字以内），帮助面试官快速了解匹配情况。

## 岗位要求
- 职位名称: {job_title}
- 学历要求: {education_req}
- 经验要求: {work_exp_req}年
- 应届/往届: {fresh_req}

## 面试者信息
- 姓名: {name}
- 学历: {education}
- 工作经验: {work_experience}年
- 应届/往届: {is_fresh}
- 技能: {skills}

如果面试者某项不满足要求，以"警示："开头；如果满足，以"匹配:"开头。
只返回备注文本，不要返回其他内容。"""

CONTENT_ANALYSIS_PROMPT = """你是一位面试评估专家。请分析以下面试回答的转写文本和语调特征，给出内容分析评价。

## 面试题目
{question_text}

## 面试者回答（语音转写）
{transcript}

## 语调特征
{tone_features}

请从以下角度分析（100字以内）：
1. 回答是否切题
2. 逻辑是否清晰
3. 表达是否流畅
4. 语调反映的自信程度

只返回分析文本，不要返回其他内容。"""

REPORT_ASSESSMENT_PROMPT = """你是一位资深HR总监。请根据以下面试信息，生成一份结构化的面试评估报告。

## 面试者: {interviewee_name}
## 应聘岗位: {job_title}

## 面试回答汇总
{answers_summary}

请严格按以下JSON格式返回评估结果，不要包含其他内容:
{{
  "answer_summary": "对面试者整体回答的概括性总结（100字以内）",
  "highlights": "面试者的亮点（分条列出，用换行分隔）",
  "risks": "面试者的风险点（分条列出，用换行分隔）",
  "recommendation": "录用建议（一句话）",
  "skill_score": 85,
  "communication_score": 80,
  "logic_score": 82,
  "culture_score": 78
}}

评分标准：
- skill_score: 专业技能（0-100）
- communication_score: 沟通能力（0-100）
- logic_score: 逻辑思维（0-100）
- culture_score: 文化匹配（0-100）"""