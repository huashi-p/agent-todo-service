import json

from application_service import dump
from evidence_service import match_resume_evidence


def build_preparation_plan(application_id):
    matched = json.loads(
        match_resume_evidence(application_id)
    )

    if "matches" not in matched:
        return dump(matched)

    drafts = []

    for item in matched["matches"]:
        requirement = item["requirement"]

        if item["match_status"] == "missing":
            drafts.append(
                {
                    "title": f"补充学习：{requirement}",
                    "task_type": "skill_gap",
                    "note": "岗位要求尚未找到证据支持",
                }
            )
        elif item["match_status"] == "partial":
            drafts.append(
                {
                    "title": f"核对证据：{requirement}",
                    "task_type": "interview_preparation",
                    "note": "已有部分证据，需要补充或准备讲解",
                }
            )

    if not drafts:
        drafts.append(
            {
                "title": "准备岗位和项目证据讲解",
                "task_type": "interview_preparation",
                "note": "当前要求均有证据支持",
            }
        )

    return dump(
        {
            "ok": True,
            "application_id": int(application_id),
            "tasks": drafts,
            "requires_confirmation": True,
        }
    )