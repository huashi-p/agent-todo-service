import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


test_db = Path(tempfile.gettempdir()) / "offerflow_tools_test.db"

if test_db.exists():
    test_db.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{test_db.as_posix()}"


from application_service import (
    create_application,
    delete_application,
    list_applications,
)
from evidence_service import (
    add_evidence_document,
    match_resume_evidence,
)

from evidence_service import (
    add_evidence_document,
    match_resume_evidence,
)
from reflection_service import reflect_match_result

from database import engine
from models import ApplicationStatusEvent, JobApplication
from status_service import (
    list_due_applications,
    update_application_status,
)

import json
from sqlalchemy import select
from sqlalchemy.orm import Session


created = json.loads(
    create_application(
        company="示例科技",
        title="AI Agent 开发实习生",
        description="要求熟悉 Python、FastAPI 和 RAG。",
        requirements=[
            "熟悉 FastAPI",
            "有 RAG 项目经验",
            "具备 Rust 开发经验",
        ],
        confirmed=True,
    )
)

assert created["ok"] is True
application_id = created["application_id"]

duplicate = json.loads(
    create_application(
        company="示例科技",
        title="AI Agent 开发实习生",
        description="这是用于测试重复检测的完整岗位描述。",
        confirmed=True,
    )
)

assert duplicate["error_code"] == "duplicate_application"


unconfirmed = json.loads(
    update_application_status(
        application_id=application_id,
        new_status="assessment",
        confirmed=False,
    )
)

assert unconfirmed["error_code"] == "confirmation_required"


blocked = json.loads(
    update_application_status(
        application_id=application_id,
        new_status="offer",
        confirmed=True,
    )
)

assert blocked["error_code"] == "invalid_transition"

updated = json.loads(
    update_application_status(
        application_id=application_id,
        new_status="assessment",
        note="收到测评通知",
        confirmed=True,
    )
)

assert updated["ok"] is True

with Session(engine) as db:
    events = db.scalars(
        select(ApplicationStatusEvent).where(
            ApplicationStatusEvent.application_id == application_id
        )
    ).all()

assert len(events) == 1
assert events[0].from_status == "applied"
assert events[0].to_status == "assessment"
assert events[0].note == "收到测评通知"


now = datetime.now(timezone.utc)

with Session(engine) as db:
    application = db.get(JobApplication, application_id)
    application.deadline = now + timedelta(days=3)
    application.updated_at = now - timedelta(days=30)
    db.commit()

deadline_result = json.loads(
    list_due_applications(due_days=7, stale_days=14)
)

assert any(
    item["id"] == application_id
    for item in deadline_result["due"]
)
assert any(
    item["id"] == application_id
    for item in deadline_result["stale"]
)


document = json.loads(
    add_evidence_document(
        kind="project",
        title="OfferFlow 项目证据",
        project_name="OfferFlow",
        source_label="README",
        content=(
            "OfferFlow 使用 FastAPI 构建 Agent API。\n\n"
            "项目使用 PostgreSQL 保存投递状态，"
            "并通过 RAG 检索项目证据。"
        ),
    )
)

assert document["ok"] is True

matched = json.loads(
    match_resume_evidence(application_id=application_id)
)

status_by_requirement = {
    item["requirement"]: item["match_status"]
    for item in matched["matches"]
}

assert status_by_requirement["熟悉 FastAPI"] == "matched"
assert status_by_requirement["有 RAG 项目经验"] == "matched"
assert status_by_requirement["具备 Rust 开发经验"] == "missing"
assert status_by_requirement == {
    "熟悉 FastAPI": "matched",
    "有 RAG 项目经验": "matched",
    "具备 Rust 开发经验": "missing",
}
reflection = json.loads(
    reflect_match_result(matched)
)

assert reflection["ok"] is True
assert reflection["issues"] == []
matched["matches"][0]["evidence"] = []

broken_reflection = json.loads(
    reflect_match_result(matched)
)

assert broken_reflection["ok"] is False
assert any(
    "没有证据" in issue
    for issue in broken_reflection["issues"]
)

assert json.loads(list_applications())["count"] == 1

delete_blocked = json.loads(
    delete_application(application_id=application_id)
)
assert delete_blocked["error_code"] == "confirmation_required"

deleted = json.loads(
    delete_application(
        application_id=application_id,
        confirmed=True,
    )
)
assert deleted["ok"] is True
assert json.loads(list_applications())["count"] == 0


rejected_app = json.loads(
    create_application(
        company="状态测试公司",
        title="终态岗位",
        description="用于验证 rejected 是终态，不能继续流转。",
        confirmed=True,
    )
)
rejected_id = rejected_app["application_id"]

first_update = json.loads(
    update_application_status(
        application_id=rejected_id,
        new_status="rejected",
        confirmed=True,
    )
)
assert first_update["ok"] is True

closed = json.loads(
    update_application_status(
        application_id=rejected_id,
        new_status="assessment",
        confirmed=True,
    )
)
assert closed["error_code"] == "invalid_transition"


print("OfferFlow 工具测试通过")
