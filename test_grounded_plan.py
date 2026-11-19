import pytest
import asyncio
import json
from types import SimpleNamespace
import grounded_plan_service

from grounded_plan_service import validate_grounded_payload


SOURCES = [
    {
        "source_id": "RESOURCE_1",
        "title": "Docker Guide",
        "url": "https://example.com/docker",
        "final_url": "https://example.com/docker",
        "fetched_at": "2026-11-18T10:00:00+00:00",
        "excerpt": "Docker packages applications into containers.",
        "search_score": 0.9,
    }
]


def test_valid_citation_is_verified():
    payload = {
        "citations": [
            {
                "source_id": "RESOURCE_1",
            }
        ]
    }

    result = validate_grounded_payload(payload, SOURCES)

    assert len(result) == 1
    assert result[0]["source_id"] == "RESOURCE_1"
    assert result[0]["url"] == "https://example.com/docker"
    assert result[0]["evidence_quote"] == SOURCES[0]["excerpt"]


def test_unknown_source_id_is_rejected():
    payload = {
        "citations": [
            {
                "source_id": "RESOURCE_99",
            }
        ]
    }

    with pytest.raises(
        ValueError,
        match="不存在的 source_id",
    ):
        validate_grounded_payload(payload, SOURCES)


def test_server_fills_evidence_quote():
    payload = {
        "citations": [
            {
                "source_id": "RESOURCE_1",
            }
        ]
    }

    result = validate_grounded_payload(payload, SOURCES)

    assert result[0]["evidence_quote"] == SOURCES[0]["excerpt"]

def test_playbook_uses_curated_template(monkeypatch):
    base_item = {
        "requirement": "Docker 容器部署",
        "playbook_key": "docker",
        "current_status": "missing",
        "current_evidence": [],
        "title": "Docker 技能进阶",
        "objective": "掌握容器部署",
        "target_level": "L3",
        "prerequisites": [],
        "steps": ["完成容器练习"],
        "exercise": "构建一个 Docker 镜像",
        "deliverable": "Dockerfile 和运行记录",
        "acceptance_criteria": ["镜像可以运行"],
        "estimated_hours": 4,
        "sources": [],
        "status": "draft",
    }

    template = {
        "application_id": 1,
        "ok": False,
        "items": [],
        "unsupported": [],
        "total_hours": 0,
        "estimated_weeks": 0,
        "validation_errors": [],
        "requires_confirmation": True,
        "saved": False,
    }

    async def fake_candidates(application_id, hours):
        return template, [base_item]

    async def fake_resources(
        requirement,
        target_level,
        search_topics=None,
    ):
        return {
            "ok": False,
            "status": "search_failed",
            "error": "模拟搜索失败",
            "sources": [],
            "failed": [],
        }

    monkeypatch.setattr(
        grounded_plan_service,
        "build_plan_candidates",
        fake_candidates,
    )
    monkeypatch.setattr(
        grounded_plan_service,
        "collect_learning_resources",
        fake_resources,
    )
    monkeypatch.setattr(
        grounded_plan_service,
        "cache_set",
        lambda *args, **kwargs: None,
    )

    result = asyncio.run(
        grounded_plan_service.build_grounded_learning_plan(
            1,
            available_hours_per_week=10,
        )
    )

    assert result["items"][0]["resource_status"] == (
        "curated_template"
    )
    assert result["items"][0]["sources"] == []
    assert result["resource_errors"][0]["status"] == (
        "search_failed"
    )


def test_model_failure_uses_basic_fallback(monkeypatch):
    base_item = {
        "requirement": "产品需求分析",
        "current_status": "missing",
        "current_evidence": [],
        "title": "产品需求分析学习建议",
        "objective": "掌握基础需求分析",
        "target_level": "L3",
        "prerequisites": [],
        "steps": ["阅读资料", "完成练习"],
        "exercise": "整理一个需求清单",
        "deliverable": "需求分析文档",
        "acceptance_criteria": ["能区分用户需求"],
        "estimated_hours": 4,
        "sources": [],
        "status": "draft",
    }

    template = {
        "application_id": 2,
        "ok": False,
        "items": [],
        "unsupported": [],
        "total_hours": 0,
        "estimated_weeks": 0,
        "validation_errors": [],
        "requires_confirmation": True,
        "saved": False,
    }

    async def fake_candidates(application_id, hours):
        return template, [base_item]

    async def fake_resources(
        requirement,
        target_level,
        search_topics=None,
    ):
        return {
            "ok": False,
            "status": "no_search_results",
            "error": "",
            "sources": [],
            "failed": [],
        }

    async def fake_model_only(item):
        raise RuntimeError("模拟模型失败")

    monkeypatch.setattr(
        grounded_plan_service,
        "build_plan_candidates",
        fake_candidates,
    )
    monkeypatch.setattr(
        grounded_plan_service,
        "collect_learning_resources",
        fake_resources,
    )
    monkeypatch.setattr(
        grounded_plan_service,
        "generate_model_only_item",
        fake_model_only,
    )
    monkeypatch.setattr(
        grounded_plan_service,
        "cache_set",
        lambda *args, **kwargs: None,
    )

    result = asyncio.run(
        grounded_plan_service.build_grounded_learning_plan(
            2,
            available_hours_per_week=10,
        )
    )

    item = result["items"][0]

    assert item["resource_status"] == "basic_fallback"
    assert item["sources"] == []
    assert item["quality_note"] == "基础步骤骨架，未联网验证"
    assert result["resource_errors"][0]["status"] == (
        "no_search_results"
    )

def test_generate_model_only_item(monkeypatch):
    base_item = {
        "requirement": "产品需求分析",
        "current_status": "missing",
        "current_evidence": [],
        "title": "产品需求分析学习建议",
        "objective": "掌握基础需求分析",
        "target_level": "L3",
        "prerequisites": [],
        "steps": ["阅读资料"],
        "exercise": "整理需求清单",
        "deliverable": "需求文档",
        "acceptance_criteria": ["能区分用户需求"],
        "estimated_hours": 4,
        "sources": [],
        "status": "draft",
    }

    payload = {
        "steps": ["学习需求分析", "完成案例练习"],
        "exercise": "分析一个真实产品需求",
        "deliverable": "需求分析文档",
        "acceptance_criteria": ["能说明需求优先级"],
        "estimated_hours": 6,
    }

    async def fake_create(*args, **kwargs):
        message = SimpleNamespace(
            content=json.dumps(payload, ensure_ascii=False)
        )
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=fake_create
            )
        )
    )
    monkeypatch.setattr(
        grounded_plan_service,
        "client",
        fake_client,
    )

    item = asyncio.run(
        grounded_plan_service.generate_model_only_item(
            base_item
        )
    )

    assert item["resource_status"] == "model_only"
    assert item["quality_note"] == "未通过联网资料验证"
    assert item["sources"] == []
    assert item["estimated_hours"] == 6
    assert item["steps"] == payload["steps"]

@pytest.mark.parametrize(
    ("playbook_key", "expected_status"),
    [
        ("docker", "curated_grounded"),
        (None, "generated_grounded"),
    ],
)
def test_enhance_item_with_sources(
    monkeypatch,
    playbook_key,
    expected_status,
):
    base_item = {
        "requirement": "Docker 容器部署",
        "current_status": "missing",
        "current_evidence": [],
        "title": "Docker 学习建议",
        "objective": "掌握容器基础",
        "target_level": "L3",
        "prerequisites": [],
        "steps": ["阅读资料"],
        "exercise": "构建镜像",
        "deliverable": "Dockerfile",
        "acceptance_criteria": ["镜像可运行"],
        "estimated_hours": 4,
        "sources": [],
        "status": "draft",
    }
    if playbook_key:
        base_item["playbook_key"] = playbook_key

    payload = {
        "steps": ["学习 Docker", "构建并运行镜像"],
        "exercise": "构建一个最小镜像",
        "deliverable": "Dockerfile 和运行记录",
        "acceptance_criteria": ["镜像能够成功启动"],
        "citations": [
            {
                "source_id": "RESOURCE_1",
            }
        ],
    }

    async def fake_create(*args, **kwargs):
        message = SimpleNamespace(
            content=json.dumps(
                payload,
                ensure_ascii=False,
            )
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
        grounded_plan_service,
        "client",
        fake_client,
    )

    item = asyncio.run(
        grounded_plan_service.enhance_item_with_sources(
            base_item,
            SOURCES,
        )
    )

    assert item["resource_status"] == expected_status
    assert len(item["sources"]) == 1
    assert item["sources"][0]["source_id"] == "RESOURCE_1"
    assert item["sources"][0]["url"] == "https://example.com/docker"
    assert item["sources"][0]["evidence_quote"] == (
        SOURCES[0]["excerpt"]
    )


def test_plan_candidates_exclude_non_learning_requirements(
    monkeypatch,
):
    matched = {
        "matches": [
            {
                "requirement": "接受加班和调休",
                "category": "work_condition",
                "match_status": "not_applicable",
                "evidence": [],
                "reason": "工作条件需本人确认",
            },
            {
                "requirement": "熟悉 Excel",
                "category": "tool_skill",
                "match_status": "missing",
                "evidence": [],
                "reason": "简历没有 Excel 证据",
            },
        ]
    }
    template = {
        "application_id": 8,
        "ok": True,
        "items": [],
        "unsupported": [],
        "total_hours": 0,
        "estimated_weeks": 0,
        "validation_errors": [],
        "requires_confirmation": True,
        "saved": False,
    }

    async def fake_match(application_id):
        return json.dumps(matched, ensure_ascii=False)

    monkeypatch.setattr(
        grounded_plan_service,
        "match_resume_evidence_with_model",
        fake_match,
    )
    monkeypatch.setattr(
        grounded_plan_service,
        "build_learning_plan",
        lambda application_id, hours: json.dumps(
            template,
            ensure_ascii=False,
        ),
    )

    result_template, candidates = asyncio.run(
        grounded_plan_service.build_plan_candidates(
            8,
            available_hours=10,
        )
    )

    assert len(candidates) == 1
    assert candidates[0]["category"] == "tool_skill"
    assert candidates[0]["requirement"] == "熟悉 Excel"
    assert len(result_template["planning_exclusions"]) == 1
    assert (
        result_template["planning_exclusions"][0]["category"]
        == "work_condition"
    )


def test_tool_fallback_is_role_neutral():
    match = {
        "requirement": "熟悉岗位所需设计工具",
        "category": "tool_skill",
        "match_status": "missing",
        "evidence": [],
        "search_topics": [
            "设计工具基础操作",
            "设计协作流程",
        ],
        "reason": "简历没有相关工具证据",
    }

    item = grounded_plan_service.make_generic_base(
        match,
        available_hours=10,
    )

    assert item["category"] == "tool_skill"
    assert "岗位实际使用的工具" in item["steps"][0]
    assert "代码" not in item["exercise"]
    assert "可运行" not in item["exercise"]
    assert "最小任务" in item["exercise"]
    assert item["search_topics"] == [
        "设计工具基础操作",
        "设计协作流程",
    ]

def test_string_citation_is_supported():
    payload = {
        "citations": ["RESOURCE_1"]
    }

    result = validate_grounded_payload(payload, SOURCES)

    assert len(result) == 1
    assert result[0]["source_id"] == "RESOURCE_1"
    assert result[0]["evidence_quote"] == (
        SOURCES[0]["excerpt"]
    )