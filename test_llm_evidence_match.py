import asyncio
import json
import pytest
from types import SimpleNamespace

import llm_evidence_match


def test_model_match_parses_response(monkeypatch):
    payload = {
        "matches": [
            {
                "requirement_index": 0,
                "category": "education",
                "match_status": "matched",
                "evidence_ids": [4],
                "search_topics": [],
                "reason": "简历显示本科",
            }
        ]
    }

    async def fake_create(*args, **kwargs):
        message = SimpleNamespace(
            content=json.dumps(payload, ensure_ascii=False)
        )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message)]
        )

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=fake_create
            )
        )
    )
    monkeypatch.setattr(
        llm_evidence_match,
        "get_client",
        lambda: fake_client,
    )

    result = asyncio.run(
        llm_evidence_match.match_requirements_with_model(
            ["大专及以上学历"],
            [
                {
                    "evidence_id": 4,
                    "document_title": "我的简历",
                    "content": "本科，软件工程专业",
                }
            ],
        )
    )

    assert result == payload


def test_unknown_evidence_id_is_rejected():
    payload = {
        "matches": [
            {
                "requirement_index": 0,
                "category": "education",
                "match_status": "matched",
                "evidence_ids": [999],
                "reason": "模型编造证据",
            }
        ]
    }

    with pytest.raises(
        ValueError,
        match="不存在的 evidence_id",
    ):
        llm_evidence_match.validate_match_payload(
            payload,
            ["大专及以上学历"],
            [
                {
                    "evidence_id": 4,
                    "document_title": "我的简历",
                    "content": "本科，软件工程专业",
                }
            ],
        )


def test_work_condition_is_forced_to_not_applicable():
    payload = {
        "matches": [
            {
                "requirement_index": 0,
                "category": "work_condition",
                "match_status": "partial",
                "evidence_ids": [4],
                "search_topics": ["非法搜索主题"],
                "reason": "模型错误地进行了匹配",
            }
        ]
    }

    result = llm_evidence_match.validate_match_payload(
        payload,
        ["接受加班和调休"],
        [
            {
                "evidence_id": 4,
                "document_title": "我的简历",
                "content": "可以接受项目高峰期加班",
            }
        ],
    )

    match = result["matches"][0]
    assert match["match_status"] == "not_applicable"
    assert match["evidence_ids"] == []
    assert match["search_topics"] == []
    assert "工作条件" in match["reason"]


def test_search_topics_reject_urls():
    payload = {
        "matches": [
            {
                "requirement_index": 0,
                "category": "tool_skill",
                "match_status": "missing",
                "evidence_ids": [],
                "search_topics": [
                    "Excel 数据透视表",
                    "Excel VLOOKUP",
                    "https://invalid.example",
                ],
                "reason": "简历没有办公软件证据",
            }
        ]
    }

    with pytest.raises(
        ValueError,
        match="search_topics 不能包含 URL",
    ):
        llm_evidence_match.validate_match_payload(
            payload,
            ["熟悉 Excel"],
            [
                {
                    "evidence_id": 4,
                    "document_title": "我的简历",
                    "content": "Python 项目经历",
                }
            ],
        )


def test_build_match_result_uses_server_evidence():
    application = {
        "id": 5,
        "company": "测试公司",
        "title": "运营助理",
        "requirements": ["大专及以上学历"],
    }
    evidence_chunks = [
        {
            "evidence_id": 4,
            "document_id": 2,
            "document_title": "我的简历",
            "project_name": None,
            "chunk_index": 0,
            "content": "本科，软件工程专业",
            "source_label": "我的简历",
        }
    ]
    payload = {
        "matches": [
            {
                "requirement_index": 0,
                "category": "education",
                "match_status": "matched",
                "evidence_ids": [4],
                "reason": "本科符合大专及以上学历",
            }
        ]
    }

    result = llm_evidence_match.build_match_result(
        payload,
        application,
        evidence_chunks,
    )

    match = result["matches"][0]
    assert match["requirement"] == "大专及以上学历"
    assert match["match_status"] == "matched"
    assert match["match_method"] == "llm_verified"
    assert match["evidence"][0]["evidence_id"] == 4
    assert match["evidence"][0]["quote"] == "本科，软件工程专业"

