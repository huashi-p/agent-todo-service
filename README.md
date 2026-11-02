# OfferFlow

一个求职投递跟踪与证据匹配 Agent。用户可以保存岗位和截止日期、
更新投递状态、记录简历与项目证据，并让 Agent 解释哪些岗位要求有
证据支持、哪些存在技能缺口。

## 项目状态

当前为 Week 8 本地版本，已有上下文预算、领域工具、状态历史、
轻量证据检索和自动化测试。公网服务器仍可能运行旧版本，部署更新
前不要用线上地址判断最新功能。

## 在线演示

- 流式聊天页面：http://123.207.78.167:8002/static/chat.html
- FastAPI Swagger：http://123.207.78.167:8002/docs

> 当前为个人演示环境，使用公网 IP 和 HTTP，不包含真实用户密码或敏感数据。

## 功能

- 岗位投递记录的创建、查询和删除
- 公司岗位指纹去重
- 投递状态机和独立状态历史
- 即将截止和长期未跟进查询
- 简历、项目和笔记证据切分与保存
- 岗位要求与证据匹配，返回 `matched`、`partial`、`missing`
- 六个 Agent Function Calling 工具
- 聊天历史、token 预算、旧历史摘要和 SSE
- PostgreSQL 持久化、Redis 缓存和 Docker Compose

## Agent 工具

```text
create_application
delete_application
update_application_status
list_due_applications
add_evidence_document
match_resume_evidence
```

## 架构

```text
浏览器
  │ HTTP :8002
  ▼
Nginx
  │ 限流 + 反向代理
  ▼
FastAPI app :8003
  ├── DeepSeek API
  ├── PostgreSQL
  └── Redis

```

## ReAct 流程

```text
用户问题
→ 模型判断是否需要调用工具
→ 返回 tool_calls
→ 执行工具并把结果加入 messages
→ 再次请求模型
→ 没有新的 tool_calls 时返回答案
```

服务包含最大循环次数、模型超时、未知工具处理、参数解析错误和工具异常降级。

## 技术栈

- Python 3.13
- FastAPI、Pydantic
- OpenAI SDK，调用 DeepSeek OpenAI-compatible API
- PostgreSQL 16、SQLAlchemy、Psycopg 3
- Redis 7
- Docker、Docker Compose
- Nginx
- Ubuntu 24.04 LTS

## 本地运行

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

> 只有 `.env` 不存在时才执行。已有 `.env` 时直接编辑，不要覆盖。

在 `.env` 中填写：

```text
DEEPSEEK_API_KEY=你的密钥
APP_PORT=8002
```

启动服务：

```powershell
docker compose up -d --build
docker compose ps
```

打开：

```text
http://127.0.0.1:8002/docs
http://127.0.0.1:8002/static/chat.html
```

## 环境变量

| 变量 | 说明 |
|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 |
| `APP_PORT` | 应用映射到宿主机的端口 |
| `DATABASE_URL` | PostgreSQL 连接串 |
| `REDIS_URL` | Redis 完整连接地址，优先使用 |
| `REDIS_HOST` | Redis 主机名，未设置 `REDIS_URL` 时使用 |
| `REDIS_PORT` | Redis 端口，默认 6379 |
| `CONTEXT_TOKEN_BUDGET` | 上下文 token 预算，默认 6000 |
| `SUMMARY_TOKEN_BUDGET` | 旧历史摘要预算，默认 800 |
| `RECENT_MESSAGE_LIMIT` | 保留的最近消息数，默认 20 |

## 测试

测试使用临时 SQLite 数据库，不会修改正式 PostgreSQL 数据：

```powershell
cd D:\code\api
D:\code\api\.venv\Scripts\python.exe test_offerflow_tools.py
```

该测试覆盖创建、重复检测、确认保护、状态机、状态历史、截止和
长期未跟进查询、证据匹配、查询与删除。

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/ask/stream` | Agent 流式提问，返回 SSE |
| POST | `/users` | 创建用户 |
| GET | `/users` | 查询用户列表 |
| GET | `/users/{user_id}` | 查询用户及其任务 |
| DELETE | `/users/{user_id}` | 删除用户 |
| POST | `/todos` | 创建任务 |
| GET | `/todos` | 查询任务列表 |
| GET | `/todos/page` | 分页查询 |
| GET | `/todos/count` | 统计任务数量 |
| GET | `/todos/{todo_id}` | 查询单个任务 |
| PATCH | `/todos/{todo_id}/done` | 修改完成状态 |
| DELETE | `/todos/{todo_id}` | 删除任务 |

## SSE 事件

```text
event: status
data: 正在思考

event: token
data: 深

event: done
data: [DONE]
```

流式响应关闭了 Nginx 代理缓冲，因此 token 事件会逐步传给浏览器。

## 缓存策略

- `GET /todos` 查询成功后写入 Redis
- 缓存键为 `todos:all`
- 默认 TTL 为 30 秒
- 创建、修改、删除任务后清除缓存
- Redis 异常时降级为直接查询 PostgreSQL

## 部署

- 云服务器：腾讯云 Lighthouse
- 系统：Ubuntu 24.04 LTS
- 应用容器仅绑定 `127.0.0.1:8003`
- Nginx 对公网监听 8002
- Nginx 使用 `proxy_buffering off` 支持 SSE
- Nginx 按 IP 执行基础请求限流
- PostgreSQL 数据保存在 Docker 命名卷
- Compose 服务使用 `restart: unless-stopped`

## 已知限制

- 指纹只用公司和岗位名，可能误判不同城市的同名岗位。
- `confirmed` 是模型生成的布尔参数，不是强用户认证。
- 轻量检索依赖关键词和手写别名，不支持语义向量召回。
- 匹配结果不代表录用概率。
- 当前流式为最终答案逐字发送，不是模型原生 token 流式。
- 单实例部署，没有多副本和用户登录鉴权。
- 领域任务表、提醒任务和复杂 RAG 尚未实现。
