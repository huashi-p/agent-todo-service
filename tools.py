from application_service import create_application, delete_application
from status_service import (
    list_due_applications,
    update_application_status,
)

from evidence_service import (
    add_evidence_document,
    match_resume_evidence,
)


TOOL_FUNCTIONS = {
    "create_application": create_application,
    "delete_application": delete_application,
    "update_application_status": update_application_status,
    "list_due_applications": list_due_applications,
    "add_evidence_document": add_evidence_document,
    "match_resume_evidence": match_resume_evidence,
}


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
