# OfferFlow 搜索 API 真实样例

**采集日期**：2026-11-13  
**搜索服务**：Tavily  
**调用接口**：`GET /api/search/preview`  
**最多结果数**：5  
**说明**：以下标题、URL、摘要和结果数量来自真实接口响应；耗时由本机在完整 HTTP 调用外测得。

---

## 样例 1：RAG 检索

- 输入查询：`RAG 检索`
- 搜索耗时：`1201.87 ms`
- 返回结果数：`5`

### 1. 什么是检索增强生成 (RAG)？| RAG 全面指南 | Elastic

- URL：https://www.elastic.co/cn/what-is/retrieval-augmented-generation
- 摘要摘录：

> 检索 RAG 从输入查询开始。这可以是用户的问题，或者需要详细回复的任意一段文本。检索模型会从知识库、数据库或外部来源抓取相关信息。检索到的信息会被转化为高维度空间中的向量，并存储在向量数据库中。

### 2. rag-web-ui/docs/tutorial/README.md at main

- URL：https://github.com/rag-web-ui/rag-web-ui/blob/main/docs/tutorial/README.md
- 摘要摘录：

> RAG 的典型应用场景包括企业知识库问答、法律法规和论文等需要权威来源或证据的回答，以及任何需要带有引用信息的回答场景。

### 3. 高级 RAG 技术 | Google Codelabs

- URL：https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/8-advanced-rag-methods/advanced-rag-methods?hl=zh-cn
- 摘要摘录：

> 检索器负责查找相关片段，重排序器负责选择最佳结果，生成器负责将零散片段组合成连贯且可读的句子。

### 4. 什么是 RAG？— 检索增强生成 AI 详解 — AWS

- URL：https://aws.amazon.com/cn/what-is/retrieval-augmented-generation
- 摘要摘录：

> LLM 原始训练数据集之外的数据称为外部数据。Embedding 技术将数据转换为数字表示并存入向量数据库，随后根据用户查询检索相关信息并增强提示词。

### 5. RAG 快速入门 | Google Cloud Documentation

- URL：https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/rag-engine/rag-quickstart?hl=zh-cn
- 摘要摘录：

> 示例展示了 RAG 检索配置，包括使用 `retrieve_contexts` 获取上下文，以及把 RAG 检索工具与生成模型结合。

---

## 样例 2：FastAPI 依赖注入

- 输入查询：`FastAPI 依赖注入`
- 搜索耗时：`773.74 ms`
- 返回结果数：`5`

### 1. 依赖项 - FastAPI - FastAPI 框架

- URL：https://fastapi.org.cn/tutorial/dependencies
- 摘要摘录：

> FastAPI 拥有一个强大且直观的依赖注入系统。依赖注入是指路径操作函数声明其正常工作所需的事物，由框架负责提供这些依赖项。

### 2. Dependencies - FastAPI

- URL：https://fastapi.tiangolo.com/tutorial/dependencies
- 摘要摘录：

> FastAPI has a very powerful but intuitive Dependency Injection system.

### 3. 依赖项 - FastAPI 中文文档

- URL：https://fastapi.tiangolo.com/zh/tutorial/dependencies
- 摘要摘录：

> 依赖注入用于共享业务逻辑、数据库连接、安全认证和权限要求，同时减少代码重复。

### 4. 如何在 FastAPI 正确使用依赖注入 - So1n blog

- URL：https://so1n.me/2023/12/07/how-to-use-dependency-injection-in-fastapi
- 摘要摘录：

> 文章介绍 `Containers`、`Providers`、`Wiring`、`Provide` 和 `Depends` 等依赖注入组织方式。

### 5. FastAPI 与依赖注入模式

- URL：https://blog.shabbywu.cn/posts/2020/11/24/fastapi%E4%B8%8E%E4%BE%9D%E8%B5%96%E6%B3%A8%E5%85%A5%E6%A8%A1%E5%BC%8F.html
- 摘要摘录：

> 文章从依赖图和组成根模式讲解 FastAPI 依赖注入的构造与注入过程。

---

## 当前观察

1. 两组查询都返回了 5 条带真实 URL 的结果。
2. `FastAPI 依赖注入` 的第一条结果来自 `fastapi.org.cn`，第二条和第三条来自 FastAPI 官方域名，说明搜索排序不完全等同于来源权威性排序。
3. Week 11 只验证搜索预览，没有抓取结果网页，也没有写入学习计划或保存来源。
4. Week 12 必须重新校验 URL、抓取正文、验证引用原文，并记录失败来源。
