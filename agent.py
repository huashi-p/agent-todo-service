import asyncio
import json
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from tools import TOOL_FUNCTIONS, TOOLS

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


async def run_agent(question, max_steps=5):
    messages = [
        {"role": "system", "content": "你是一个助手。需要查天气或算数或时间时，调用给你的工具。"},
        {"role": "user", "content": question},
    ]

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
    print(asyncio.run(run_agent("深圳和北京今天分别多少度？相差几度？")))