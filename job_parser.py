import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import ValidationError

from schemas import ParsedJob

load_dotenv(Path(__file__).resolve().parent / ".env")

client = AsyncOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


async def parse_job_description(description):
    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "从岗位描述中提取结构化信息，只输出 JSON。"
                    "不要猜测原文没有的信息。"
                    "deadline 必须是 ISO 8601 或 null。"
                    "requirements 只保存具体技能、经验和资格要求。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "返回 company、title、location、source_url、"
                    "deadline、requirements。\n\n"
                    + description
                ),
            },
        ],
        temperature=0,
        max_tokens=1200,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"

    try:
        return ParsedJob.model_validate_json(content)
    except ValidationError as e:
        raise ValueError(f"岗位解析结果格式错误：{e}") from e