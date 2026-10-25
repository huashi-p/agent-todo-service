# Agent Todo Service

一个手写 ReAct Agent 与任务管理服务。Agent 支持天气查询、数学计算和当前时间工具；服务集成 PostgreSQL、Redis 缓存、SSE 流式输出、Docker Compose 和 Nginx 反向代理。

## 项目状态

当前为 Week 6 工程基础版本，完成了 Agent API、数据库、缓存、流式输出和公网部署。

后续计划加入真实领域工具、多轮对话、上下文压缩、RAG、搜索引用、评测和请求额度控制。

## 在线演示

- 流式聊天页面：http://123.207.78.167:8002/static/chat.html
- FastAPI Swagger：http://123.207.78.167:8002/docs

> 当前为个人演示环境，使用公网 IP 和 HTTP，不包含真实用户密码或敏感数据。

## 功能

- 手写 ReAct 循环，支持多轮 function calling
- 天气查询、数学计算、当前时间三个工具
- SSE 流式输出最终答案
- FastAPI 用户与任务 CRUD
- SQLAlchemy ORM 一对多关系
- PostgreSQL 数据持久化
- Redis 列表缓存，包含 TTL 和写后失效
- Redis 故障时降级查询数据库
- Docker Compose 管理 API、PostgreSQL 和 Redis
- Nginx 反向代理与请求限流
- Docker 服务自动重启
- 公网 Ubuntu 服务器部署

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

- 天气工具使用示例数据
- 当前流式为最终答案逐字发送，不是模型原生 token 流式
- 单实例部署，没有多副本
- 暂无用户登录鉴权
- 使用 HTTP 公网演示，不传输敏感数据
- 尚未完成真实领域 RAG 和 Agent 评测