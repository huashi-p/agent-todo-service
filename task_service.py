from sqlalchemy import select
from sqlalchemy.orm import Session

from application_service import dump, parse_datetime, tool_error
from database import engine
from models import ApplicationTask, JobApplication


TASK_TYPES = {
    "skill_gap",
    "interview_preparation",
    "follow_up",
    "assessment",
}


def create_application_task(
    application_id,
    title,
    task_type="interview_preparation",
    due_at=None,
    note="",
    confirmed=False,
):
    if not confirmed:
        return tool_error(
            "confirmation_required",
            "创建任务前需要用户确认",
        )

    if task_type not in TASK_TYPES:
        return tool_error("invalid_arguments", "任务类型不合法")

    if not title.strip():
        return tool_error("invalid_arguments", "任务标题不能为空")

    with Session(engine) as db:
        application = db.get(JobApplication, int(application_id))

        if application is None:
            return tool_error("not_found", "没有这个投递记录")

        existing = db.scalar(
            select(ApplicationTask).where(
                ApplicationTask.application_id == application.id,
                ApplicationTask.title == title.strip(),
                ApplicationTask.status == "pending",
            )
        )

        if existing is not None:
            return tool_error(
                "duplicate_task",
                f"已有相同待办任务，ID 为 {existing.id}",
            )

        task = ApplicationTask(
            application_id=application.id,
            title=title.strip(),
            task_type=task_type,
            due_at=parse_datetime(due_at),
            note=note.strip(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        return dump(
            {
                "ok": True,
                "task_id": task.id,
                "application_id": task.application_id,
                "title": task.title,
                "task_type": task.task_type,
                "status": task.status,
            }
        )


def list_application_tasks(application_id, include_done=False):
    with Session(engine) as db:
        stmt = select(ApplicationTask).where(
            ApplicationTask.application_id == int(application_id)
        )

        if not include_done:
            stmt = stmt.where(ApplicationTask.status == "pending")

        tasks = db.scalars(
            stmt.order_by(ApplicationTask.created_at)
        ).all()

    return dump(
        {
            "ok": True,
            "count": len(tasks),
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "task_type": task.task_type,
                    "due_at": (
                        task.due_at.isoformat()
                        if task.due_at
                        else None
                    ),
                    "status": task.status,
                }
                for task in tasks
            ],
        }
    )


def complete_application_task(task_id, confirmed=False):
    if not confirmed:
        return tool_error(
            "confirmation_required",
            "完成任务前需要用户确认",
        )

    with Session(engine) as db:
        task = db.get(ApplicationTask, int(task_id))

        if task is None:
            return tool_error("not_found", "没有这个任务")

        task.status = "done"
        db.commit()

    return dump({"ok": True, "task_id": int(task_id)})
