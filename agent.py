import asyncio
import json
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from context import SUMMARY_TOKEN_BUDGET, build_context
from tools import TOOL_FUNCTIONS, TOOLS


load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


async def summarize_history(messages):
    lines = []

    for message in messages:
        role = "用户" if message["role"] == "user" else "助手"
        lines.append(f"{role}：{message['content']}")

    transcript = "\n".join(lines)
    transcript = truncate_transcript(transcript)

    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "把下面的对话压缩成事实摘要。保留用户目标、"
                    "已经确认的信息、未完成事项和重要约束。"
                    "不要补充原文没有的信息。"
                ),
            },
            {"role": "user", "content": transcript},
        ],
        temperature=0,
        max_tokens=SUMMARY_TOKEN_BUDGET,
    )

    return response.choices[0].message.content or ""


def truncate_transcript(transcript):
    if len(transcript) <= 16000:
        return transcript

    head = transcript[:7000]
    tail = transcript[-7000:]
    return head + "\n[中间旧消息已省略]\n" + tail


async def run_agent(question, history=None, max_steps=5):
    bundle = await build_context(
        question,
        history or [],
        summarize_history,
    )
    messages = bundle.messages

    for step in range(1, max_steps + 1):
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=TOOLS,
            temperature=0,
        )

        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content

        for call in msg.tool_calls:
            name = call.function.name

            try:
                args = json.loads(call.function.arguments)
            except json.JSONDecodeError:
                result = f"参数格式不对：{call.function.arguments}"
            else:
                func = TOOL_FUNCTIONS.get(name)

                if func is None:
                    result = f"没有这个工具：{name}"
                else:
                    try:
                        result = func(**args)
                    except Exception as e:
                        result = f"工具执行出错：{e}"

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
                }
            )

    return "达到最大轮数，还没得出答案"


if __name__ == "__main__":
    print(asyncio.run(run_agent("请记住：我正在找深圳的AI Agent实习。")))