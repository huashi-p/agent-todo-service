from sqlalchemy import select
from sqlalchemy.orm import Session

from application_service import dump, normalize_text, tool_error
from database import engine
from models import (
    EvidenceChunk,
    EvidenceDocument,
    JobApplication,
)


SKILL_ALIASES = {
    "python": ["python"],
    "fastapi": ["fastapi", "web api", "接口开发"],
    "rag": ["rag", "检索增强", "知识库问答", "向量检索"],
    "agent": ["agent", "智能体", "工具调用", "function calling"],
    "postgresql": ["postgresql", "postgres", "pgsql"],
    "redis": ["redis", "缓存"],
    "docker": ["docker", "容器"],
    "asyncio": ["asyncio", "异步编程", "协程"],
}

def requirement_terms(requirement):
    normalized = normalize_text(requirement)
    terms = set()

    for aliases in SKILL_ALIASES.values():
        normalized_aliases = [
            normalize_text(alias)
            for alias in aliases
        ]

        if any(alias in normalized for alias in normalized_aliases):
            terms.update(normalized_aliases)

    english_tokens = normalized.split()
    terms.update(
        token.strip(".,:;()[]{}，。；：（）")
        for token in english_tokens
        if len(token) >= 2
    )

    return {term for term in terms if term}

def has_direct_skill_match(requirement, content):
    requirement_text = normalize_text(requirement)
    content_text = normalize_text(content)

    for aliases in SKILL_ALIASES.values():
        normalized_aliases = [
            normalize_text(alias)
            for alias in aliases
        ]

        requirement_has_skill = any(
            alias in requirement_text
            for alias in normalized_aliases
        )
        content_has_skill = any(
            alias in content_text
            for alias in normalized_aliases
        )

        if requirement_has_skill and content_has_skill:
            return True

    return False


def rank_evidence(requirement, chunks, top_k=3):
    terms = requirement_terms(requirement)
    normalized_requirement = normalize_text(requirement)
    ranked = []

    for chunk in chunks:
        searchable = normalize_text(chunk["content"])
        direct_match = has_direct_skill_match(
            requirement,
            chunk["content"],
        )
        matched_terms = {
            term
            for term in terms
            if term in searchable
        }
        phrase_match = normalized_requirement in searchable

        if not matched_terms and not direct_match:
            continue

        coverage = (
            len(matched_terms) / len(terms)
            if terms
            else 0
        )
        ranked.append(
            {
                "chunk": chunk,
                "score": len(matched_terms),
                "coverage": coverage,
                "matched_terms": sorted(matched_terms),
                "direct_match": direct_match,
                "phrase_match": phrase_match,
            }
        )

    ranked.sort(
        key=lambda item: (
            item["direct_match"],
            item["phrase_match"],
            item["score"],
            item["coverage"],
            -item["chunk"]["id"],
        ),
        reverse=True,
    )

    selected = []
    seen_content = set()

    for item in ranked:
        fingerprint = normalize_text(item["chunk"]["content"])

        if fingerprint in seen_content:
            continue

        seen_content.add(fingerprint)
        selected.append(item)

        if len(selected) >= top_k:
            break

    return selected


def match_resume_evidence(application_id, top_k=3):
    top_k = max(1, min(int(top_k), 5))

    with Session(engine) as db:
        application = db.get(JobApplication, int(application_id))

        if application is None:
            return tool_error("not_found", "没有这个投递记录")

        rows = db.execute(
            select(EvidenceChunk, EvidenceDocument).join(
                EvidenceDocument,
                EvidenceChunk.document_id == EvidenceDocument.id,
            )
        ).all()

        application_data = {
            "id": application.id,
            "company": application.company,
            "title": application.title,
            "requirements": list(application.requirements or []),
        }
        chunks = [
            {
                "id": chunk.id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "document_id": document.id,
                "document_title": document.title,
                "project_name": document.project_name,
                "source_label": document.source_label,
            }
            for chunk, document in rows
        ]

        matches = []

        for requirement in application_data["requirements"]:
            selected = rank_evidence(
                requirement,
                chunks,
                top_k,
            )
            if not selected:
                match_status = "missing"
            elif selected[0]["direct_match"] or selected[0]["score"] >= 2:
                match_status = "matched"
            else:
                match_status = "partial"

            evidence = [
                {
                    "evidence_id": item["chunk"]["id"],
                    "document_id": item["chunk"]["document_id"],
                    "document_title": item["chunk"]["document_title"],
                    "project_name": item["chunk"]["project_name"],
                    "chunk_index": item["chunk"]["chunk_index"],
                    "quote": item["chunk"]["content"][:500],
                    "source_label": item["chunk"]["source_label"],
                    "matched_terms": item["matched_terms"],
                }
                for item in selected
            ]

            matches.append(
                {
                    "requirement": requirement,
                    "match_status": match_status,
                    "evidence": evidence,
                }
            )

        return dump(
            {
                "application_id": application_data["id"],
                "company": application_data["company"],
                "title": application_data["title"],
                "matches": matches,
                "note": "这是可解释的本地证据检索，不代表录用概率。",
            }
        )


def split_evidence_text(text, max_chars=700):
    cleaned = text.replace("\r\n", "\n").strip()
    paragraphs = [
        part.strip()
        for part in cleaned.split("\n\n")
        if part.strip()
    ]

    chunks = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""

            for start in range(0, len(paragraph), max_chars):
                chunks.append(
                    paragraph[start:start + max_chars].strip()
                )
            continue

        candidate = (
            paragraph
            if not current
            else current + "\n\n" + paragraph
        )

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)

    return chunks


def add_evidence_document(
    kind,
    title,
    content,
    project_name=None,
    source_label=None,
):
    if kind not in {"resume", "project", "note"}:
        return tool_error("invalid_arguments", "kind 不合法")

    if len(title.strip()) < 1 or len(content.strip()) < 20:
        return tool_error("invalid_arguments", "标题或正文过短")

    chunks = split_evidence_text(content)

    with Session(engine) as db:
        document = EvidenceDocument(
            kind=kind,
            title=title.strip(),
            project_name=project_name,
            source_label=source_label,
            content=content.strip(),
        )
        db.add(document)
        db.flush()

        for index, chunk in enumerate(chunks):
            db.add(
                EvidenceChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk,
                )
            )

        db.commit()
        document_id = document.id

    return dump(
        {
            "ok": True,
            "document_id": document_id,
            "chunk_count": len(chunks),
        }
    )
