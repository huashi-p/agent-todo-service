from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from application_service import dump, tool_error
from database import engine
from models import ApplicationStatusEvent, JobApplication


ACTIVE_STATUSES = {
    "applied",
    "assessment",
    "first_interview",
    "second_interview",
    "hr_interview",
}

STATUS_TRANSITIONS = {
    "applied": {
        "assessment",
        "first_interview",
        "rejected",
        "withdrawn",
    },
    "assessment": {
        "first_interview",
        "rejected",
        "withdrawn",
    },
    "first_interview": {
        "second_interview",
        "hr_interview",
        "offer",
        "rejected",
        "withdrawn",
    },
    "second_interview": {
        "hr_interview",
        "offer",
        "rejected",
        "withdrawn",
    },
    "hr_interview": {
        "offer",
        "rejected",
        "withdrawn",
    },
    "offer": set(),
    "rejected": set(),
    "withdrawn": set(),
}


def update_application_status(
    application_id,
    new_status,
    note="",
    confirmed=False,
):
    if not confirmed:
        return tool_error(
            "confirmation_required",
            "修改状态前必须得到用户明确确认",
        )

    with Session(engine) as db:
        item = db.get(JobApplication, int(application_id))

        if item is None:
            return tool_error("not_found", "没有这个投递记录")

        old_status = item.current_status
        allowed = STATUS_TRANSITIONS.get(old_status, set())

        if new_status not in allowed:
            return tool_error(
                "invalid_transition",
                f"不能从 {old_status} 直接变更为 {new_status}",
            )

        item.current_status = new_status
        item.updated_at = datetime.now(timezone.utc)

        db.add(
            ApplicationStatusEvent(
                application_id=item.id,
                from_status=old_status,
                to_status=new_status,
                note=note.strip(),
            )
        )
        db.commit()

    return dump(
        {
            "ok": True,
            "application_id": int(application_id),
            "from_status": old_status,
            "to_status": new_status,
        }
    )


def list_due_applications(due_days=7, stale_days=14):
    now = datetime.now(timezone.utc)
    due_until = now + timedelta(days=due_days)
    stale_before = now - timedelta(days=stale_days)

    with Session(engine) as db:
        items = db.scalars(
            select(JobApplication).where(
                JobApplication.current_status.in_(ACTIVE_STATUSES)
            )
        ).all()

    due = []
    stale = []

    for item in items:
        deadline = item.deadline

        if deadline is not None:
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)

            if now <= deadline <= due_until:
                due.append(
                    {
                        "id": item.id,
                        "company": item.company,
                        "title": item.title,
                        "deadline": deadline.isoformat(),
                    }
                )

        updated_at = item.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)

        if updated_at <= stale_before:
            stale.append(
                {
                    "id": item.id,
                    "company": item.company,
                    "title": item.title,
                    "updated_at": updated_at.isoformat(),
                }
            )

    return dump(
        {
            "ok": True,
            "due": due,
            "stale": stale,
        }
    )