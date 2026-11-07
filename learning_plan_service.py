import json

from application_service import dump, normalize_text
from evidence_service import SKILL_ALIASES, match_resume_evidence
from skill_catalog import SKILL_PLAYBOOKS


VALID_LEVELS = {"L1", "L2", "L3", "L4"}


def find_playbook_key(requirement):
    text = normalize_text(requirement)

    for key, aliases in SKILL_ALIASES.items():
        if key not in SKILL_PLAYBOOKS:
            continue

        if any(normalize_text(alias) in text for alias in aliases):
            return key

    return None

def validate_plan_items(items, available_hours_per_week):
    errors = []
    total_hours = sum(
        max(0, int(item.get("estimated_hours", 0)))
        for item in items
    )

    if (
        available_hours_per_week > 0
        and total_hours > available_hours_per_week
    ):
        errors.append(
            f"计划需要 {total_hours} 小时，超过每周可用 "
            f"{available_hours_per_week} 小时"
        )

    for index, item in enumerate(items, start=1):
        label = f"第 {index} 项"

        for field in ("requirement", "objective", "exercise", "deliverable"):
            if not str(item.get(field, "")).strip():
                errors.append(f"{label}缺少 {field}")

        if not item.get("steps"):
            errors.append(f"{label}缺少学习步骤")

        if not item.get("acceptance_criteria"):
            errors.append(f"{label}缺少验收标准")

        if item.get("target_level") not in VALID_LEVELS:
            errors.append(f"{label}目标等级不合法")

    return total_hours, errors

def build_learning_plan(
    application_id,
    available_hours_per_week=10,
):
    matched = json.loads(match_resume_evidence(application_id))

    if "matches" not in matched:
        return dump(matched)

    items = []
    unsupported = []

    for match in matched["matches"]:
        if match["match_status"] == "matched":
            continue

        key = find_playbook_key(match["requirement"])

        if key is None:
            unsupported.append(
                {
                    "requirement": match["requirement"],
                    "match_status": match["match_status"],
                    "reason": "还没有对应技能模板",
                }
            )
            continue

        book = SKILL_PLAYBOOKS[key]
        items.append(
            {
                "requirement": match["requirement"],
                "playbook_key": key,
                "current_status": match["match_status"],
                "current_evidence": match.get("evidence", []),
                "title": f"{key.upper()} 技能进阶",
                "objective": book["objective"],
                "target_level": book["target_level"],
                "prerequisites": list(book["prerequisites"]),
                "steps": list(book["steps"]),
                "exercise": book["exercise"],
                "deliverable": book["deliverable"],
                "acceptance_criteria": list(book["acceptance_criteria"]),
                "estimated_hours": book["estimated_hours"],
                "sources": [],
                "status": "draft",
            }
        )

    total_hours, errors = validate_plan_items(
        items,
        int(available_hours_per_week),
    )

    return dump(
        {
            "ok": not errors,
            "application_id": int(application_id),
            "items": items,
            "unsupported": unsupported,
            "total_hours": total_hours,
            "validation_errors": errors,
            "requires_confirmation": True,
            "saved": False,
        }
    )