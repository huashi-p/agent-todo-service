SKILL_PLAYBOOKS = {
    "rag": {
        "target_level": "L3",
        "objective": "能独立实现并评测带引用的 RAG 问答系统",
        "prerequisites": [
            "Python 基础",
            "HTTP/API 基础",
        ],
        "steps": [
            "理解文档切分、Embedding 和向量召回",
            "实现检索 Top-K 和来源引用",
            "建立 20 条问答评测样例",
            "分析召回失败并调整切分或检索参数",
        ],
        "exercise": "实现一个小型技术文档 RAG 问答系统。",
        "deliverable": "可运行的 RAG 项目、评测集和失败案例说明。",
        "acceptance_criteria": [
            "能解释切分、Embedding 和 Top-K 的作用",
            "答案能引用真实检索片段",
            "能报告 Recall@K 和引用正确率",
            "能说明至少两个检索失败案例",
        ],
        "estimated_hours": 20,
    },
    "redis": {
        "target_level": "L3",
        "objective": "能为 FastAPI 查询实现可降级的 Redis 缓存",
        "prerequisites": [
            "Python 基础",
            "SQLAlchemy 查询基础",
        ],
        "steps": [
            "理解 key、TTL、缓存失效和异常降级",
            "实现查询缓存和主动失效",
            "测试命中率与 Redis 故障回退",
        ],
        "exercise": "为岗位列表增加 Redis 缓存。",
        "deliverable": "缓存代码、命中率记录和故障回退演示。",
        "acceptance_criteria": [
            "能解释缓存穿透和过期策略",
            "能展示缓存命中率测试",
            "Redis 不可用时服务仍能返回数据库结果",
        ],
        "estimated_hours": 8,
    },
}