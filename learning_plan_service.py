import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from application_service import dump, normalize_text, tool_error
from database import engine
from evidence_service import SKILL_ALIASES, match_resume_evidence
from models import (
    JobApplication,
    LearningPlanItem,
    SkillRequirement,
)
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

    if available_hours_per_week <= 0:
        errors.append("每周可用学时必须大于 0")

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
    weekly_hours = max(1, int(available_hours_per_week))
    estimated_weeks = (
                              total_hours + weekly_hours - 1
                      ) // weekly_hours

    return dump(
        {
            "ok": not errors,
            "application_id": int(application_id),
            "items": items,
            "unsupported": unsupported,
            "total_hours": total_hours,
            "estimated_weeks": estimated_weeks,
            "validation_errors": errors,
            "requires_confirmation": True,
            "saved": False,
        }
    )

def save_learning_plan(
    application_id,
    items,
    confirmed=False,
    available_hours_per_week=10,
):
    if not confirmed:
        return tool_error(
            "confirmation_required",
            "保存学习计划前必须得到用户确认",
        )

    if not isinstance(items, list) or not items:
        return tool_error(
            "invalid_arguments",
            "学习计划不能为空",
        )

    total_hours, errors = validate_plan_items(
        items,
        int(available_hours_per_week),
    )

    if errors:
        return dump(
            {
                "ok": False,
                "error_code": "invalid_plan",
                "errors": errors,
            }
        )

    created = 0
    updated = 0

    with Session(engine) as db:
        application = db.get(JobApplication, int(application_id))

        if application is None:
            return tool_error("not_found", "没有这个投递记录")

        for draft in items:
            requirement_text = str(
                draft.get("requirement", "")
            ).strip()

            requirement = db.scalar(
                select(SkillRequirement).where(
                    SkillRequirement.application_id == application.id,
                    SkillRequirement.requirement == requirement_text,
                )
            )

            evidence_ids = [
                int(evidence["evidence_id"])
                for evidence in draft.get("current_evidence", [])
                if evidence.get("evidence_id") is not None
            ]

            if requirement is None:
                requirement = SkillRequirement(
                    application_id=application.id,
                    requirement=requirement_text,
                )
                db.add(requirement)
                created += 1
            else:
                updated += 1

            requirement.current_status = draft["current_status"]
            requirement.target_level = draft["target_level"]
            requirement.gap_type = draft["current_status"]
            requirement.evidence_ids = evidence_ids
            db.flush()

            plan = db.scalar(
                select(LearningPlanItem).where(
                    LearningPlanItem.application_id == application.id,
                    LearningPlanItem.requirement_id == requirement.id,
                )
            )

            plan_values = {
                "title": draft["title"],
                "objective": draft["objective"],
                "target_level": draft["target_level"],
                "steps": list(draft["steps"]),
                "exercise": draft["exercise"],
                "deliverable": draft["deliverable"],
                "acceptance_criteria": list(
                    draft["acceptance_criteria"]
                ),
                "sources": list(draft.get("sources", [])),
                "estimated_hours": int(draft["estimated_hours"]),
            }

            if plan is None:
                plan = LearningPlanItem(
                    application_id=application.id,
                    requirement_id=requirement.id,
                    **plan_values,
                )
                db.add(plan)
            else:
                for field, value in plan_values.items():
                    setattr(plan, field, value)

        db.commit()

        return dump(
            {
                "ok": True,
                "saved": True,
                "application_id": int(application_id),
                "count": len(items),
                "created_requirements": created,
                "updated_requirements": updated,
                "total_hours": total_hours,
            }
        )

def save_generated_learning_plan(
    application_id,
    available_hours_per_week=10,
    confirmed=False,
):
    if not confirmed:
        return tool_error(
            "confirmation_required",
            "保存学习计划前必须得到用户确认",
        )

    draft = json.loads(
        build_learning_plan(
            application_id,
            available_hours_per_week,
        )
    )

    if not draft.get("items"):
        return dump(
            {
                "ok": False,
                "error_code": "no_supported_plan",
                "message": "当前没有可生成的技能模板",
                "unsupported": draft.get("unsupported", []),
            }
        )

    return save_learning_plan(
        application_id,
        draft["items"],
        confirmed=confirmed,
        available_hours_per_week=available_hours_per_week,
    )