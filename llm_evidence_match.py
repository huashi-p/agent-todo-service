import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

from requirement_policy import (
    CATEGORY_DEFINITIONS,
    CATEGORY_POLICY,
    get_category_policy,
)


load_dotenv(Path(__file__).resolve().parent / ".env")

MATCH_CATEGORIES = set(CATEGORY_POLICY)

MATCH_STATUSES = {
    "matched",
    "partial",
    "missing",
    "not_applicable",
}


def build_match_messages(
    requirements,
    evidence_chunks,
    job_description="",
):
    requirement_payload = [
        {
            "requirement_index": index,
            "requirement": str(requirement),
        }
        for index, requirement in enumerate(requirements)
    ]
    evidence_payload = []

    for item in evidence_chunks:
        evidence_id = item.get("evidence_id")

        if evidence_id is None:
            evidence_id = item.get("id")

        if evidence_id is None:
            raise ValueError("证据缺少 evidence_id")

        evidence_payload.append(
            {
                "evidence_id": int(evidence_id),
                "title": item.get("document_title", ""),
                "content": str(item.get("content", ""))[:1200],
            }
        )

    request_payload = {
        "requirements": requirement_payload,
        "evidence": evidence_payload,
        "job_description": str(job_description)[:3000],
        "allowed_categories": sorted(MATCH_CATEGORIES),
        "allowed_statuses": sorted(MATCH_STATUSES),
        "category_definitions": CATEGORY_DEFINITIONS,
    }

    system_prompt = (
        "你是岗位要求分类与候选人证据匹配器。"
        "先判断每条要求的类别，再决定是否允许匹配。"
        "只能根据给定证据判断，不得补充证据中没有的经历。"
        "不得修改岗位要求。"
        "只能引用输入中真实存在的 evidence_id。"
        "只有技术技能、工具技能、行业知识和实践经历"
        "可以进行 matched、partial、missing 判断。"
        "软技能、主观态度、工作条件和其他非学习要求"
        "的 match_status 必须为 not_applicable，"
        "evidence_ids 必须为空。"
        "性格、沟通、团队合作、热爱、积极、责任心、抗压"
        "不得根据简历判断。"
        "加班、调休、出差、轮班、驻场、地点等属于工作条件。"
        "对于可匹配的技术技能、工具技能、行业知识和实践经历，"
        "可以结合岗位 JD 输出 1 到 3 个具体 search_topics。"
        "search_topics 必须是适合搜索学习资料的具体主题，"
        "不能是整段岗位要求，不能包含 URL。"
        "matched、not_applicable 和非学习要求"
        "的 search_topics 必须为空数组。"
        "例如岗位提到 Excel 报表和 SKU 数据时，"
        "可以输出 Excel 数据透视表、Excel VLOOKUP、"
        "SKU 库存台账等主题。"
        "matched 必须至少引用一个 evidence_id；"
        "partial 表示只满足部分要求；"
        "没有相关证据时必须返回 missing。"
        "学历要求需要比较学历层级。"
        "无法可靠分类时使用 unknown，且不得匹配。"
        "只输出 JSON。"
        "输出格式为："
        '{"matches":[{"requirement_index":0,'
        '"category":"education",'
        '"match_status":"matched",'
        '"evidence_ids":[12],'
        '"search_topics":[],'
        '"reason":"简要说明"}]}'
    )

    user_prompt = (
        "请逐条匹配以下岗位要求和证据，返回 JSON：\n"
        + json.dumps(
            request_payload,
            ensure_ascii=False,
            indent=2,
        )
    )

    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

client = None


def get_client():
    global client

    if client is not None:
        return client

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=os.getenv(
            "DEEPSEEK_BASE_URL",
            "https://api.deepseek.com",
        ),
    )
    return client


async def match_requirements_with_model(
    requirements,
    evidence_chunks,
    job_description="",
):
    messages = build_match_messages(
        requirements,
        evidence_chunks,
        job_description=job_description,
    )

    response = await get_client().chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        messages=messages,
        temperature=0,
        max_tokens=1800,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("模型没有返回合法 JSON") from error

    if not isinstance(payload, dict):
        raise ValueError("模型返回结果不是 JSON 对象")

    if not isinstance(payload.get("matches"), list):
        raise ValueError("模型结果缺少 matches 数组")

    return validate_match_payload(
        payload,
        requirements,
        evidence_chunks,
    )

def validate_match_payload(
    payload,
    requirements,
    evidence_chunks,
):
    matches = payload.get("matches")

    if not isinstance(matches, list):
        raise ValueError("模型结果缺少 matches 数组")

    expected_indexes = set(range(len(requirements)))
    valid_evidence_ids = {
        int(item.get("evidence_id", item.get("id")))
        for item in evidence_chunks
    }

    normalized = []
    seen_indexes = set()

    for match in matches:
        if not isinstance(match, dict):
            raise ValueError("matches 中存在非对象结果")

        try:
            requirement_index = int(
                match["requirement_index"]
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                "模型返回了非法 requirement_index"
            ) from error

        if requirement_index not in expected_indexes:
            raise ValueError("requirement_index 超出岗位要求范围")

        if requirement_index in seen_indexes:
            raise ValueError("requirement_index 重复")

        category = match.get("category")
        if category not in MATCH_CATEGORIES:
            raise ValueError("模型返回了非法要求分类")

        status = match.get("match_status")
        if status not in MATCH_STATUSES:
            raise ValueError("模型返回了非法匹配状态")

        policy = get_category_policy(category)
        evidence_ids = match.get("evidence_ids", [])
        search_topics = match.get("search_topics", [])

        normalized_ids = []
        normalized_topics = []
        reason = str(match.get("reason", ""))[:500]

        if not policy["matchable"]:
            status = "not_applicable"
            reason = policy["exclusion_reason"]
        else:
            if status == "not_applicable":
                raise ValueError(
                    "可匹配分类不能使用 not_applicable"
                )

            if not isinstance(evidence_ids, list):
                raise ValueError("evidence_ids 必须是数组")

            for value in evidence_ids:
                try:
                    evidence_id = int(value)
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        "evidence_id 必须是整数"
                    ) from error

                if evidence_id not in valid_evidence_ids:
                    raise ValueError(
                        "模型引用了不存在的 evidence_id"
                    )

                if evidence_id not in normalized_ids:
                    normalized_ids.append(evidence_id)

            if status in {"matched", "partial"} and not normalized_ids:
                raise ValueError(
                    "matched 或 partial 必须提供证据"
                )

            if status == "missing":
                normalized_ids = []

            if status in {"matched", "not_applicable"}:
                normalized_topics = []
            else:
                if not isinstance(search_topics, list):
                    raise ValueError(
                        "search_topics 必须是数组"
                    )

                for topic in search_topics[:3]:
                    topic = str(topic).strip()[:80]

                    if not topic:
                        continue

                    if topic.startswith(
                        ("http://", "https://")
                    ):
                        raise ValueError(
                            "search_topics 不能包含 URL"
                        )

                    if topic not in normalized_topics:
                        normalized_topics.append(topic)

        seen_indexes.add(requirement_index)
        normalized.append(
            {
                "requirement_index": requirement_index,
                "category": category,
                "match_status": status,
                "evidence_ids": normalized_ids,
                "search_topics": normalized_topics,
                "reason": reason,
            }
        )

    if seen_indexes != expected_indexes:
        raise ValueError("模型没有覆盖全部岗位要求")

    return {"matches": normalized}

def build_match_result(
    payload,
    application,
    evidence_chunks,
    match_method="llm_verified",
):
    evidence_map = {}

    for item in evidence_chunks:
        evidence_id = int(
            item.get("evidence_id", item.get("id"))
        )
        evidence_map[evidence_id] = item

    matches = []

    for item in payload["matches"]:
        requirement_index = item["requirement_index"]
        evidence = []

        for evidence_id in item["evidence_ids"]:
            chunk = evidence_map[evidence_id]
            evidence.append(
                {
                    "evidence_id": evidence_id,
                    "document_id": chunk["document_id"],
                    "document_title": chunk.get(
                        "document_title",
                        "",
                    ),
                    "project_name": chunk.get(
                        "project_name"
                    ),
                    "chunk_index": chunk.get(
                        "chunk_index",
                        0,
                    ),
                    "quote": chunk["content"][:500],
                    "source_label": chunk.get(
                        "source_label"
                    ),
                }
            )

        matches.append(
            {
                "requirement_index": requirement_index,
                "requirement": application[
                    "requirements"
                ][requirement_index],
                "category": item["category"],
                "match_status": item["match_status"],
                "match_method": match_method,
                "evidence": evidence,
                "search_topics": item.get(
                    "search_topics",
                    [],
                ),
                "reason": item["reason"],
            }
        )

    return {
        "application_id": application["id"],
        "company": application["company"],
        "title": application["title"],
        "matches": matches,
        "note": (
            "模型负责判断，程序已校验证据编号；"
            "匹配结果不代表录用概率。"
        ),
    }

