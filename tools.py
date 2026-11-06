from application_service import create_application, delete_application
from status_service import (
    list_due_applications,
    update_application_status,
)
from job_parser import parse_job_json
from evidence_service import (
    add_evidence_document,
    match_resume_evidence,
)
from reflection_service import reflect_match_result
from plan_service import build_preparation_plan
from task_service import (
    complete_application_task,
    create_application_task,
    list_application_tasks,
)


TOOL_FUNCTIONS = {
    "create_application": create_application,
    "delete_application": delete_application,
    "update_application_status": update_application_status,
    "list_due_applications": list_due_applications,
    "add_evidence_document": add_evidence_document,
    "match_resume_evidence": match_resume_evidence,
}

TOOL_FUNCTIONS.update(
    {
        "build_preparation_plan": build_preparation_plan,
        "create_application_task": create_application_task,
        "list_application_tasks": list_application_tasks,
        "complete_application_task": complete_application_task,
    }
)


TOOL_FUNCTIONS["parse_job_json"] = parse_job_json

TOOL_FUNCTIONS["reflect_match_result"] = reflect_match_result

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_application",
            "description": "在用户确认后创建岗位投递记录",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "location": {"type": "string"},
                    "source_url": {"type": "string"},
                    "deadline": {"type": "string"},
                    "requirements": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "confirmed": {"type": "boolean"},
                },
                "required": [
                    "company",
                    "title",
                    "description",
                    "confirmed",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_application",
            "description": "在用户确认后删除投递记录",
            "parameters": {
                "type": "object",
                "properties": {
                    "application_id": {"type": "integer"},
                    "confirmed": {"type": "boolean"},
                },
                "required": ["application_id", "confirmed"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "update_application_status",
            "description": "在用户明确确认后更新投递阶段，必须遵守状态流转规则",
            "parameters": {
                "type": "object",
                "properties": {
                    "application_id": {
                        "type": "integer",
                    },
                    "new_status": {
                        "type": "string",
                        "enum": [
                            "assessment",
                            "first_interview",
                            "second_interview",
                            "hr_interview",
                            "offer",
                            "rejected",
                            "withdrawn",
                        ],
                    },
                    "note": {
                        "type": "string",
                    },
                    "confirmed": {
                        "type": "boolean",
                    },
                },
                "required": [
                    "application_id",
                    "new_status",
                    "confirmed",
                ],
            },
        },
    },


    {
        "type": "function",
        "function": {
            "name": "list_due_applications",
            "description": "查询即将截止和长期没有更新的投递记录",
            "parameters": {
                "type": "object",
                "properties": {
                    "due_days": {
                        "type": "integer",
                        "description": "查询未来多少天内截止，默认 7 天",
                        "minimum": 1,
                        "maximum": 30,
                    },
                    "stale_days": {
                        "type": "integer",
                        "description": "查询超过多少天未更新，默认 14 天",
                        "minimum": 1,
                        "maximum": 90,
                    },
                },
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "add_evidence_document",
            "description": "保存简历、项目或笔记证据，并自动切成检索片段",
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": ["resume", "project", "note"],
                        "description": "证据类型",
                    },
                    "title": {
                        "type": "string",
                        "description": "证据标题",
                    },
                    "content": {
                        "type": "string",
                        "description": "证据正文，至少 20 个字符",
                    },
                    "project_name": {
                        "type": "string",
                        "description": "关联项目名称",
                    },
                    "source_label": {
                        "type": "string",
                        "description": "来源，例如 README 或简历",
                    },
                },
                "required": ["kind", "title", "content"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "match_resume_evidence",
            "description": "根据投递记录中的岗位要求检索简历或项目证据",
            "parameters": {
                "type": "object",
                "properties": {
                    "application_id": {
                        "type": "integer",
                        "description": "要匹配的投递记录 ID",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "每项要求最多返回几条证据，默认 3",
                        "minimum": 1,
                        "maximum": 5,
                    },
                },
                "required": ["application_id"],
            },
        },
    },
]


TOOLS.append(
    {
        "type": "function",
        "function": {
            "name": "parse_job_json",
            "description": "从岗位 JD 原文中提取结构化岗位信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "完整岗位描述原文",
                    },
                },
                "required": ["description"],
            },
        },
    }
)


TOOLS.extend(
    [
        {
            "type": "function",
            "function": {
                "name": "build_preparation_plan",
                "description": (
                    "根据岗位要求和匹配证据生成准备任务草稿，"
                    "只生成计划，不写入数据库"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "application_id": {
                            "type": "integer",
                            "description": "投递记录 ID",
                        },
                    },
                    "required": ["application_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_application_task",
                "description": (
                    "在用户确认后为岗位创建准备、跟进、"
                    "测评或技能补强任务"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "application_id": {
                            "type": "integer",
                            "description": "投递记录 ID",
                        },
                        "title": {
                            "type": "string",
                            "description": "任务标题",
                        },
                        "task_type": {
                            "type": "string",
                            "enum": [
                                "skill_gap",
                                "interview_preparation",
                                "follow_up",
                                "assessment",
                            ],
                            "description": "任务类型",
                        },
                        "due_at": {
                            "type": "string",
                            "description": (
                                "可选，ISO 8601 日期或时间，"
                                "例如 2026-11-10"
                            ),
                        },
                        "note": {
                            "type": "string",
                            "description": "任务说明",
                        },
                        "confirmed": {
                            "type": "boolean",
                            "description": "用户是否已经明确确认创建",
                        },
                    },
                    "required": [
                        "application_id",
                        "title",
                        "confirmed",
                    ],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_application_tasks",
                "description": "查询某个投递记录关联的准备和跟进任务",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "application_id": {
                            "type": "integer",
                            "description": "投递记录 ID",
                        },
                        "include_done": {
                            "type": "boolean",
                            "description": (
                                "是否包含已完成任务，默认 false"
                            ),
                        },
                    },
                    "required": ["application_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "complete_application_task",
                "description": "在用户确认后把任务标记为已完成",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "integer",
                            "description": "任务 ID",
                        },
                        "confirmed": {
                            "type": "boolean",
                            "description": "用户是否已经明确确认",
                        },
                    },
                    "required": ["task_id", "confirmed"],
                },
            },
        },
    ]
)

TOOLS.append(
    {
        "type": "function",
        "function": {
            "name": "reflect_match_result",
            "description": (
                "检查匹配结果是否满足状态和证据规则，"
                "不重新判断岗位匹配"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "match_result": {
                        "type": "object",
                        "description": (
                            "match_resume_evidence 返回的完整匹配结果"
                        ),
                    },
                },
                "required": ["match_result"],
            },
        },
    }
)

