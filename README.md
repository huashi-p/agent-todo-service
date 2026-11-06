# OfferFlow

一个求职投递跟踪与证据匹配 Agent。用户可以保存岗位和截止日期、
更新投递状态、记录简历与项目证据，并让 Agent 解释哪些岗位要求有
证据支持、哪些存在技能缺口。

## 项目状态

当前为 Week 9 MVP 本地开发版本，已完成岗位解析、投递状态、证据检索、
Reflection、任务持久化、上下文预算、SSE 和离线回归测试。

公网服务器可能仍运行旧版本，部署更新前不要用线上地址判断最新功能。
从准备任务草稿到用户确认保存的完整流程仍以 Day 62 端到端验收结果为准。
详细的 Week 9 冻结范围见 [Week 9 MVP 冻结](docs/week9-mvp-freeze.md)。

## 历史公网演示

- 流式聊天页面：http://123.207.78.167:8002/static/chat.html
- FastAPI Swagger：http://123.207.78.167:8002/docs

> 以上地址可能仍运行 Week 8 版本。Week 9 功能以本地运行和测试结果为准。
> 当前为个人演示环境，使用公网 IP 和 HTTP，不包含真实用户密码或敏感数据。

## 产品主流程

```text
粘贴岗位 JD
→ 解析并由用户确认
→ 创建投递记录
→ 保存简历或项目证据
→ 匹配岗位要求
→ 显示证据和技能缺口
→ Reflection 检查匹配结果
→ 生成准备任务草稿
→ 用户确认后保存任务
```

## 功能

- 岗位投递记录的创建、查询和删除
- 公司岗位指纹去重
- 投递状态机和独立状态历史
- 即将截止和长期未跟进查询
- 简历、项目和笔记证据切分与保存
- 岗位要求与证据匹配，返回 `matched`、`partial`、`missing`
- 证据排序、原文命中、覆盖率和重复片段去除
- Reflection 确定性检查状态与证据是否一致
- 根据技能缺口生成准备任务草稿
- 用户确认后创建、查询和完成任务
- 聊天历史、token 预算、旧历史摘要和 SSE
- PostgreSQL 持久化、Redis 缓存和 Docker Compose

User/Todo CRUD 和 Redis Todo 缓存属于工程底座，不是 OfferFlow 产品主流程。

## Agent 工具

当前注册 12 个工具：

```text
parse_job_json
create_application
delete_application
update_application_status
list_due_applications
add_evidence_document
match_resume_evidence
build_preparation_plan
create_application_task
list_application_tasks
complete_application_task
reflect_match_result
```

其中：

- `build_preparation_plan` 只生成计划草稿，不写入数据库。
- `create_application_task` 必须收到用户确认后才持久化。
- `reflect_match_result` 使用确定性规则检查证据，不重新调用模型。

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
D:\code\api\.venv\Scripts\python.exe evaluate_matching.py
```

覆盖创建、重复检测、确认保护、状态机、状态历史、截止和长期未跟进、
证据匹配、证据排序、Reflection、任务和终态回归。

匹配评估使用固定离线样例，结果不能等同于真实用户准确率。

## API

`/ask/stream` 是产品主入口。下面的 User/Todo 路由保留为工程底座，
用于证明 CRUD、数据库和 Redis 基础设施能力。

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
- 外部用户试用和真实反馈尚未完成，当前只有开发样例。
- 当前流式为最终答案逐字发送，不是模型原生 token 流式。
- 单实例部署，没有多副本和用户登录鉴权。
- 没有复杂任务看板、自动通知和多智能体功能。
