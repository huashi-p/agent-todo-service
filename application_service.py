import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from database import engine
from models import JobApplication


APP_TIMEZONE = ZoneInfo("Asia/Shanghai")


def parse_datetime(value):
    if value is None or value == "":
        return None

    parsed = datetime.fromisoformat(
        str(value).replace("Z", "+00:00")
    )

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=APP_TIMEZONE)

    return parsed.astimezone(timezone.utc)


def normalize_text(value):
    value = unicodedata.normalize("NFKC", value or "").casefold()
    return re.sub(r"\s+", " ", value).strip()


def make_fingerprint(company, title):
    raw = normalize_text(company) + "|" + normalize_text(title)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def dump(payload):
    return json.dumps(payload, ensure_ascii=False)


def tool_error(error_code, message):
    return dump(
        {
            "ok": False,
            "error_code": error_code,
            "message": message,
        }
    )

def create_application(
    company,
    title,
    description,
    location=None,
    source_url=None,
    deadline=None,
    requirements=None,
    confirmed=False,
):
    if not confirmed:
        return tool_error(
            "confirmation_required",
            "创建前必须先向用户展示结果并取得确认",
        )

    if not company.strip() or not title.strip():
        return tool_error("invalid_arguments", "公司和岗位不能为空")

    if len(description.strip()) < 10:
        return tool_error("invalid_arguments", "岗位描述太短")

    requirements = requirements or []

    if not isinstance(requirements, list):
        return tool_error("invalid_arguments", "岗位要求必须是数组")

    fingerprint = make_fingerprint(company, title)


    with Session(engine) as db:
        existing = db.scalar(
            select(JobApplication).where(
                JobApplication.fingerprint == fingerprint
            )
        )

        if existing is not None:
            return tool_error(
                "duplicate_application",
                f"该岗位可能已经存在，记录 ID 为 {existing.id}",
            )

        item = JobApplication(
            company=company.strip(),
            title=title.strip(),
            description=description.strip(),
            location=location,
            source_url=source_url,
            deadline=parse_datetime(deadline),
            current_status="applied",
            requirements=requirements,
            fingerprint=fingerprint,
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        return dump(
            {
                "ok": True,
                "message": "投递记录已创建",
                "application_id": item.id,
                "company": item.company,
                "title": item.title,
            }
        )


def list_applications(limit=20):
    with Session(engine) as db:
        items = db.scalars(
            select(JobApplication)
            .order_by(JobApplication.updated_at.desc())
            .limit(limit)
        ).all()

    return dump(
        {
            "ok": True,
                "count": len(items),
            "applications": [
                {
                    "id": item.id,
                    "company": item.company,
                    "title": item.title,
                    "current_status": item.current_status,
                }
                for item in items
            ],
        }
    )


def delete_application(application_id, confirmed=False):
    if not confirmed:
        return tool_error(
            "confirmation_required",
            "删除前必须得到用户明确确认",
        )

    with Session(engine) as db:
        item = db.get(JobApplication, application_id)

        if item is None:
            return tool_error("not_found", "没有这个投递记录")

        db.delete(item)
        db.commit()

    return dump({"ok": True, "deleted_id": application_id})