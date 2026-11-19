import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env")

SYSTEM_PROMPT = (
    "你是一个求职投递跟踪与匹配助手。"
    "涉及岗位、投递状态、截止时间、简历证据或技能匹配时，"
    "必须调用提供的工具。不能编造经历、技能、日期和投递状态。"
    "匹配结论必须说明证据和缺失项，不能承诺录用结果。"

    "生成技能计划时必须调用 build_learning_plan，"
    "并向用户展示返回的计划草稿。"
    "只能展示工具返回的 sources 链接，不能自行生成 URL。"

    "如果 resource_status 是 curated_grounded "
    "或 generated_grounded，可以展示真实来源链接，"
    "并说明计划经过了联网资料验证。"

    "如果是 curated_template，要说明没有获取到外部资料，"
    "当前使用人工模板。"

    "如果是 model_only，要说明这是 AI 基础建议，"
    "未通过联网资料验证。"

    "如果是 basic_fallback，要说明这是通用步骤骨架，"
    "外部搜索和模型生成均不可用。"

    "not_applicable 表示该要求不属于可基于简历"
    "验证的技能或经历，不能解释为用户缺失能力。"
    "软技能、性格态度和工作条件不得生成学习计划。"
    "planning_exclusions 中的要求要向用户说明"
    "为何未生成计划。"

    "unsupported 只能表示某一个要求资料不足，"
    "不能阻止其他计划项返回，也不能让整份计划失败。"

    "用户明确确认后才能调用 save_learning_plan 保存计划。"
    "用户只说“生成计划”不代表确认保存。"
)

TOKEN_BUDGET = int(os.getenv("CONTEXT_TOKEN_BUDGET", "6000"))
SUMMARY_TOKEN_BUDGET = int(os.getenv("SUMMARY_TOKEN_BUDGET", "800"))
RECENT_MESSAGE_LIMIT = int(os.getenv("RECENT_MESSAGE_LIMIT", "20"))
MESSAGE_CHAR_LIMIT = 8000
MAX_HISTORY_MESSAGES = 200
MIN_RECENT_TOKEN_BUDGET = 400


@dataclass
class ContextBundle:
    messages: list[dict]
    original_tokens: int
    final_tokens: int
    summarized_count: int


def estimate_tokens(text):
    if not text:
        return 0

    chinese_count = sum(
        1 for ch in text if "\u4e00" <= ch <= "\u9fff"
    )
    other_count = len(text) - chinese_count
    return chinese_count + math.ceil(other_count / 4)


def normalize_history(history):
    normalized = []

    for item in history or []:
        if hasattr(item, "model_dump"):
            item = item.model_dump()

        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if role not in {"user", "assistant"}:
            continue
        if not isinstance(content, str) or not content.strip():
            continue

        normalized.append(
            {
                "role": role,
                "content": content.strip()[:MESSAGE_CHAR_LIMIT],
            }
        )

    return normalized[-MAX_HISTORY_MESSAGES:]


def truncate_text(text, max_tokens):
    text = text or ""

    if estimate_tokens(text) <= max_tokens:
        return text

    if max_tokens <= 0:
        return ""

    marker = "\n[内容已截断]"

    if estimate_tokens(marker) >= max_tokens:
        return text[:max_tokens]

    low = 0
    high = len(text)

    while low < high:
        middle = (low + high + 1) // 2
        candidate = text[:middle].rstrip() + marker

        if estimate_tokens(candidate) <= max_tokens:
            low = middle
        else:
            high = middle - 1

    return text[:low].rstrip() + marker


def split_history(history, max_recent_tokens):
    selected = []
    used_tokens = 0

    for message in reversed(history):
        if len(selected) >= RECENT_MESSAGE_LIMIT:
            break

        message_tokens = estimate_tokens(message["content"]) + 4

        if selected and used_tokens + message_tokens > max_recent_tokens:
            break

        current = message

        if not selected and message_tokens > max_recent_tokens:
            content_budget = max(0, max_recent_tokens - 4)
            current = {
                "role": message["role"],
                "content": truncate_text(
                    message["content"],
                    content_budget,
                ),
            }
            message_tokens = estimate_tokens(current["content"]) + 4

        selected.append(current)
        used_tokens += message_tokens

    selected.reverse()
    recent_count = len(selected)
    older = history[:len(history) - recent_count]
    return older, selected


async def build_context(
    question,
    history,
    summarize: Callable[[list[dict]], Awaitable[str]],
):
    history = normalize_history(history)
    question = question or ""

    fixed_tokens = (
        estimate_tokens(SYSTEM_PROMPT)
        + estimate_tokens(question)
        + 8
    )
    available_tokens = TOKEN_BUDGET - fixed_tokens

    if available_tokens <= 0:
        raise ValueError("系统提示和当前问题已经超过上下文预算")

    summary_budget = min(
        SUMMARY_TOKEN_BUDGET,
        max(0, available_tokens - MIN_RECENT_TOKEN_BUDGET),
    )
    recent_budget = available_tokens - summary_budget
    older, recent = split_history(history, recent_budget)

    summary = ""
    if older:
        summary = await summarize(older)
        summary = truncate_text((summary or "").strip(), summary_budget)

    system_content = SYSTEM_PROMPT
    if summary:
        system_content += "\n\n此前对话摘要：\n" + summary

    messages = [
        {"role": "system", "content": system_content},
        *recent,
        {"role": "user", "content": question},
    ]

    original_tokens = (
        estimate_tokens(SYSTEM_PROMPT)
        + estimate_tokens(question)
        + sum(
            estimate_tokens(message["content"]) + 4
            for message in history
        )
    )
    final_tokens = sum(
        estimate_tokens(message["content"]) + 4
        for message in messages
    )

    if final_tokens > TOKEN_BUDGET:
        raise ValueError("上下文组装后仍然超过 token 预算")

    return ContextBundle(
        messages=messages,
        original_tokens=original_tokens,
        final_tokens=final_tokens,
        summarized_count=len(older),
    )
