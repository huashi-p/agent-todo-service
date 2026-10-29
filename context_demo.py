import asyncio

from context import TOKEN_BUDGET, build_context


async def fake_summary(messages):
    return f"此前共有 {len(messages)} 条消息，用户持续记录岗位和投递状态。"


async def main():
    history = []

    for turn in range(1, 101):
        history.append(
            {
                "role": "user",
                "content": f"第 {turn} 轮：岗位状态或技能证据记录。",
            }
        )
        history.append(
            {
                "role": "assistant",
                "content": f"已记录第 {turn} 条求职事项。",
            }
        )

    bundle = await build_context(
        "请根据已有记录总结当前求职投递状态。",
        history,
        fake_summary,
    )

    print("原始历史消息数：", len(history))
    print("被摘要消息数：", bundle.summarized_count)
    print("最近完整消息数：", len(bundle.messages) - 2)
    print("原始估算 token：", bundle.original_tokens)
    print("最终估算 token：", bundle.final_tokens)
    print("预算：", TOKEN_BUDGET)

    assert bundle.summarized_count > 0
    assert bundle.final_tokens <= TOKEN_BUDGET
    assert bundle.messages[0]["role"] == "system"
    assert bundle.messages[-1]["role"] == "user"
    print("100 轮上下文压测通过")


asyncio.run(main())