import asyncio
import json
import uuid

from sqlalchemy.orm import Session

import evidence_service
import llm_evidence_match
from models import (
    EvidenceChunk,
    EvidenceDocument,
    JobApplication,
    engine,
)


def test_model_failure_uses_local_fallback(monkeypatch):
    with Session(engine) as db:
        application = JobApplication(
            company="回退测试公司",
            title="Python 开发实习生",
            description="负责 Python 后端服务开发",
            requirements=["熟悉 Python 编程"],
            fingerprint=uuid.uuid4().hex,
        )
        document = EvidenceDocument(
            kind="resume",
            title="测试简历",
            source_label="测试简历",
            content="熟练使用 Python 完成接口开发。",
        )
        db.add_all([application, document])
        db.flush()

        db.add(
            EvidenceChunk(
                document_id=document.id,
                chunk_index=0,
                content="熟练使用 Python 完成接口开发。",
            )
        )
        db.commit()
        application_id = application.id

    async def fake_model_match(*args, **kwargs):
        raise RuntimeError("模拟模型失败")

    monkeypatch.setattr(
        llm_evidence_match,
        "match_requirements_with_model",
        fake_model_match,
    )

    result = json.loads(
        asyncio.run(
            evidence_service.match_resume_evidence_with_model(
                application_id
            )
        )
    )

    assert result["match_method"] == "local_fallback"
    assert "模拟模型失败" in result["fallback_reason"]
    assert result["matches"][0]["match_status"] == "matched"
    assert result["matches"][0]["category"] == "technical_skill"
    assert result["matches"][0]["match_method"] == "local_fallback"
    assert result["matches"][0]["requirement"] == (
        "熟悉 Python 编程"
    )
