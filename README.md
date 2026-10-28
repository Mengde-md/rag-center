# RAG 中台后端骨架

面向业务方提供统一 RAG 检索能力。第一阶段只实现知识库创建、纯文本同步索引、结构化召回三个业务接口。业务方拿到片段与引用后，自行调用生成模型或业务编排服务。

技术栈：Python 3.11、FastAPI、Pydantic v2、SQLAlchemy 2.0、Psycopg 3、Alembic、PostgreSQL 16、pgvector、OpenAI-compatible Embedding HTTP API。

Compose 使用 `pgvector/pgvector:0.8.1-pg16`：PostgreSQL 主版本为 16，pgvector 扩展版本为 0.8.1。

## 本地启动

### Docker Compose（推荐）

需要已运行的 Docker Engine / Docker Desktop，以及支持可选 `env_file` 的 Docker Compose 2.24+。

```powershell
cd rag-center
Copy-Item .env.example .env
# 编辑 .env，填写 MODEL_BASE_URL、MODEL_API_KEY、EMBEDDING_MODEL、EMBEDDING_DIMENSIONS
docker compose up --build -d
docker compose ps
docker compose logs api
```

API 容器启动时先执行 `alembic upgrade head`，成功后启动 Uvicorn。PostgreSQL 使用健康检查与持久化卷。默认 API 地址为 <http://localhost:8000>，交互文档为 <http://localhost:8000/docs>。

仅启动数据库时使用 `docker compose up -d postgres`。停止服务使用 `docker compose down`，已有数据库数据保留。

缺少有效模型配置时，服务和知识库创建接口仍可启动；文档上传和检索会明确返回 Embedding 配置错误。默认镜像不会注入任何测试向量或模拟模型。

### 本机 Python 3.11

```powershell
cd rag-center
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
# 编辑 .env，配置模型；DATABASE_URL 指向本机 PostgreSQL
docker compose up -d postgres
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m app
```

Linux/macOS 将虚拟环境命令路径替换为 `.venv/bin/python`、`.venv/bin/alembic`、`.venv/bin/uvicorn`，并用 `cp .env.example .env`。

启动入口 `python -m app` 可传 `--host` / `--port`。Windows 下显式使用 Selector 事件循环，以兼容 Psycopg 异步驱动；默认监听本机 127.0.0.1:8000，容器中监听 0.0.0.0:8000。

仓库包含 `uv.lock` 与导出的生产依赖 `requirements.lock`，Docker 使用后者固定运行时版本。已安装 uv 时，可执行 `uv sync --locked --extra dev --python 3.11`，同时安装锁定的运行与测试依赖。

## 配置

所有配置由 Pydantic Settings 从环境变量 / `.env` 读取，环境变量优先。完整示例见 `.env.example`。

| 配置 | 默认值 | 用途 |
| --- | --- | --- |
| APP_ENV | local | 环境标识 |
| DATABASE_URL | postgresql+psycopg://postgres:postgres@localhost:5432/rag_center | PostgreSQL 连接 |
| MODEL_BASE_URL | https://api.openai.com/v1 | Embedding 基础 URL，调用时追加 `/embeddings` |
| MODEL_API_KEY | 空 | 模型凭据，仅通过 Authorization 请求头发送 |
| EMBEDDING_MODEL | text-embedding-3-small | Embedding 模型标识 |
| EMBEDDING_DIMENSIONS | 1536 | 模型原生输出维度与数据库 vector 维度 |
| EMBEDDING_BATCH_SIZE | 32 | 每次模型请求的最大文本数量 |
| MODEL_TIMEOUT_SECONDS | 60 | 单次模型 HTTP 请求超时秒数 |
| VECTOR_STORE | pgvector | 向量库实现选择 |
| CHUNK_SIZE / CHUNK_OVERLAP | 800 / 100 | Unicode 字符窗口大小与重叠字符数 |
| TOP_K | 5 | 最大召回数量 |
| MAX_CONTENT_LENGTH | 100000 | 单次上传的最大内容字符数 |
| POSTGRES_PORT / API_PORT | 5432 / 8000 | Compose 映射到本机的端口 |

Compose 自动把 API 容器中的数据库地址改为 `postgres:5432`。从宿主机连接数据库时，`.env` 的 DATABASE_URL 端口须与 POSTGRES_PORT 一致。

MODEL_BASE_URL 在启动时校验：必须使用 HTTP/HTTPS、具有主机和有效端口，且不能包含账号密码、空白字符、查询参数或片段。仍支持本地 HTTP 端点和 `/v1` 等路径前缀，末尾斜杠会统一移除。模型凭据应单独填写 MODEL_API_KEY；配置异常文本不回显原始配置值。

切片按字符计数，保留规范化文本的 `start_char` / `end_char` 和 `chunk_index`。Embedding Provider 分批请求，按上游 `index` 恢复顺序，校验向量数量、维度、有限值及非零向量。为兼容不同服务，默认请求仅发送 `model`、`input`、`encoding_format=float`，不发送厂商专有参数或 `dimensions`；因此 EMBEDDING_DIMENSIONS 应匹配模型实际输出维度。

初始迁移根据 EMBEDDING_DIMENSIONS 建立向量列及 HNSW cosine 索引，支持 1–2000 维。**建库后更换模型或修改维度需要新增迁移并重新索引全部文档**，即使新旧模型维度相同，也不能混用语义空间。启动时检查数据库向量列维度，发现与配置不一致会直接报错。

## 三个业务接口

仅暴露以下三个业务操作。`/docs`、`/redoc`、`/openapi.json` 为 FastAPI 文档设施。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| POST | /api/v1/knowledge-bases/create | 创建知识库 |
| POST | /api/v1/documents/upload | 接收 JSON 纯文本，同步切片、Embedding、向量写入 |
| POST | /api/v1/rag/retrieve | 生成 query 向量、召回 chunk、记录日志 |

成功格式为 `{"code":0,"msg":"success","data":{...}}`，错误格式为 `{"code":非零,"msg":"可读错误","data":null或错误详情}`。保留正常 HTTP 语义：参数错误 422、知识库不存在 404、内容过长 413、模型故障 502、内部错误 500。框架的 404/405 和未处理错误也使用该格式。

上传正文不能为空白；开头的 UTF-8 BOM 标记不算正文。移除开头 BOM 后仅剩空白的内容会在请求校验阶段返回 HTTP 422（业务码 `42201`），不进入索引流程；含正文的 BOM 文本仍交给解析器统一处理标记和换行。

### 1. 创建知识库

```json
{
  "name": "退款政策知识库",
  "description": "用于客服退款问题问答",
  "tenant_id": "tenant_demo"
}
```

返回 `data.kb_id`、`name`、`tenant_id`、`created_at`。kb_id 为中台生成的 UUID；时间为带时区的 ISO 8601。

### 2. 上传纯文本

```json
{
  "tenant_id": "tenant_demo",
  "kb_id": "替换为创建接口返回的 UUID",
  "title": "退款政策",
  "content": "用户可在订单完成后 7 天内申请退款。"
}
```

第一版选择纯文本 JSON 方式。`.txt` / `.md` 可由调用方读取后放入 `content`；Markdown 保留为原文，不做复杂格式解析。kb_id 放在请求 body 中。

成功返回 `document_id`、`kb_id`、`status: 1`、`chunk_count`。同步流程为：

1. 验证知识库的 tenant_id；创建并提交 PROCESSING 文档记录。
2. IndexingService 解析文本、切片、批量 Embedding、调用 VectorStore。
3. 在同一事务中写入 chunk 并将文档改为 SUCCESS，再提交。
4. 发生索引错误时回滚 chunk 事务，在独立事务中持久化 FAILED 与安全的 error_message。

失败响应示例：

```json
{
  "code": 50202,
  "msg": "embedding provider timed out",
  "data": {
    "document_id": "00000000-0000-4000-8000-000000000001",
    "status": 2,
    "chunk_count": 0
  }
}
```

状态枚举固定为 `1=SUCCESS`、`2=FAILED`、`3=PROCESSING`。请求失败后保留 document_id 便于排查；不另加状态查询接口。进程被强制终止可能留下 PROCESSING 记录，后续异步任务阶段可增加超时恢复与重试。数据库本身不可用时，无法保证失败状态立即落库。

### 3. RAG 检索增强

```json
{
  "tenant_id": "tenant_demo",
  "kb_id": "替换为创建接口返回的 UUID",
  "user_id": "user_demo",
  "query": "退款需要几天内申请？"
}
```

`data` 包含 `query`、`kb_id`、`retrieved_chunks` 与 `metadata`。每个 chunk 包含 document_id、chunk_id、title、content、score、metadata（切片序号与字符位置等引用元数据）。外层 metadata 包含 top_k、vector_store、retrieval_log_id。

按余弦相似度 `1 - cosine_distance` 降序返回，分数范围为 [-1, 1]，不代表概率。只召回当前租户、当前知识库、已成功索引文档的 chunk。HNSW 为近似检索，启用 pgvector 0.8+ 的迭代扫描以改善过滤后的召回；在大数据量下仍需评测和调优。空知识库返回空列表。

每次成功检索记录 user_id、原始 query、召回 chunk、top_k、vector_store、耗时及时间，并通过 retrieval_log_id 关联。没有 `context_text` 字段，也不调用生成模型。

### PowerShell 最小闭环

```powershell
$base = 'http://localhost:8000/api/v1'
$kb = Invoke-RestMethod -Method Post -Uri "$base/knowledge-bases/create" `
  -ContentType 'application/json; charset=utf-8' `
  -Body (@{name='退款政策'; tenant_id='tenant_demo'} | ConvertTo-Json)
$kbId = $kb.data.kb_id
Invoke-RestMethod -Method Post -Uri "$base/documents/upload" `
  -ContentType 'application/json; charset=utf-8' `
  -Body (@{tenant_id='tenant_demo'; kb_id=$kbId; title='退款政策'; content='用户可在订单完成后 7 天内申请退款。'} | ConvertTo-Json)
Invoke-RestMethod -Method Post -Uri "$base/rag/retrieve" `
  -ContentType 'application/json; charset=utf-8' `
  -Body (@{tenant_id='tenant_demo'; kb_id=$kbId; user_id='user_demo'; query='退款需要几天内申请？'} | ConvertTo-Json) `
  | ConvertTo-Json -Depth 10
```

## 目录与分层

```text
app/
  api/v1/routes/        # 三个 HTTP 接口：仅处理入参、出参与依赖注入
  api/dependencies.py  # 组装实现的唯一入口
  core/                # .env 配置、日志、统一异常响应
  db/                  # ORM Base、异步会话、启动时维度检查
  models/              # KnowledgeBase、Document、Chunk、RetrievalLog
  schemas/             # Pydantic v2 请求与响应
  services/            # 业务编排及事务边界；独立 IndexingService
  repositories/        # 数据库读写；方法 flush，不自行提交事务
  providers/
    embedding/         # EmbeddingProvider + OpenAICompatibleEmbeddingProvider
    vectorstores/      # VectorStore + PgVectorStore
    parsers/           # DocumentParser + PlainTextParser
  utils/               # UUID 生成、TextSplitter + CharacterTextSplitter
  main.py              # FastAPI lifespan 与资源释放
migrations/            # Alembic 版本管理与初始迁移
tests/                 # 契约、模型协议、切片、真实数据库集成测试
docker-compose.yml     # PostgreSQL 16 + pgvector 和 API
Dockerfile
pyproject.toml
.env.example
```

Service 仅依赖 EmbeddingProvider、VectorStore、DocumentParser、TextSplitter 抽象；具体向量库在依赖组装处选择。VectorStore 提供 add_chunks、similarity_search、delete_by_document_id，均保留明确租户范围。当前 pgvector 实现使用同一个 SQLAlchemy 会话保证原子性；接入外部向量库时应在适配层增加补偿删除或 outbox/幂等任务方案，不能假设跨数据库共享事务。

tenant_id、user_id 由业务方提供；kb_id、document_id、chunk_id、retrieval_log_id 通过 `utils/id_generator.py` 统一生成 UUID。复合外键保证文档与 chunk 的租户及知识库归属。tenant_id 过滤提供数据隔离，但第一阶段没有身份认证，调用方身份和 tenant_id 的绑定需由接入网关负责；user_id 只记录日志，不实现 ACL。

## Alembic

首次建表：`alembic upgrade head`。查看版本：`alembic current`。

修改 ORM 后生成下一版迁移，再审查并执行：

```powershell
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head
alembic check
```

只生成 SQL：`alembic upgrade head --sql`。回退上一版：`alembic downgrade -1`，初始版本的回退会删除四张业务表。

迁移会执行 `CREATE EXTENSION IF NOT EXISTS vector`。首次部署需要拥有安装扩展权限的数据库账号；已有受管 PostgreSQL 时可由管理员预先安装。应用启动只验证已有表，不通过 `create_all` 隐式建表。

## 测试

当前环境实际执行的检查及未验证项见 [VERIFICATION.md](VERIFICATION.md)。

```powershell
.\.venv\Scripts\python.exe -m pytest -m "not integration"
.\.venv\Scripts\ruff.exe check .
```

真实集成测试需要独立测试数据库，数据库名必须以 `_test` 结尾。每个用例在随机独立 schema 中执行真实 Alembic 迁移，结束后只清理该 schema，保留测试数据库及 vector 扩展。

```powershell
docker compose up -d postgres
docker compose exec postgres createdb -U postgres rag_center_test
$env:TEST_DATABASE_URL = 'postgresql+psycopg://postgres:postgres@localhost:5432/rag_center_test'
.\.venv\Scripts\python.exe -m pytest
```

测试覆盖三个接口的最小闭环、真实 cosine 排序、调用日志落库、租户/知识库隔离、Embedding 失败、实际 chunk INSERT 后回滚及 FAILED 状态持久化。集成测试中的 EmbeddingProvider 使用确定性测试向量，不产生外部模型费用；OpenAI-compatible HTTP 协议另通过 MockTransport 验证分批、顺序、异常与维度检查。生产启动始终使用真实的 OpenAI-compatible Provider。未设置 TEST_DATABASE_URL 时集成用例会明确显示为 skipped。

## 自动检查

推送到 `main` 或提交 Pull Request 时，[GitHub Actions](.github/workflows/ci.yml) 会在 Python 3.11 下按 `uv.lock` 安装运行与开发依赖，执行 Ruff 静态检查、格式检查，以及不依赖真实数据库的业务测试和 Day01 契约实验。也可以在 Actions 页面手动运行。

本地执行相同检查：

```bash
uv sync --locked --extra dev
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pytest tests "docs/学习单元/第一阶段/Day01_实验/test_day01_contract.py" -m "not integration" -q
```

这些检查不需要真实模型密钥，不会替代 PostgreSQL/pgvector 集成验证或真实模型调用验证。

## 学习与交接

现有项目的技术栈基线、源码走读、事务边界、学习路线和交接入口见 [学习与交接文档](docs/README.md)。学习按 3 阶段、20 个核心学习日安排，默认每天 2–3 小时、约 4 周；当前已开启第一阶段 Day01，完整教材与实验已提供。

## 后续扩展

- 接入 Elasticsearch / OpenSearch，实现 BM25 与向量混合检索。
- 将 IndexingService 迁移到 BackgroundTasks、Celery 或消息队列，增加幂等、重试、超时恢复与任务状态。
- 增加 RerankProvider。
- 增加 Milvus / Qdrant / Elastic VectorStore 实现。
- 增加身份认证与 ACL 过滤，将 user_id 传入检索权限策略。
- 增加评测集、用户反馈与质量闭环。
- 增加管理后台。

本阶段不包含管理页面、多格式解析、混合检索、rerank、复杂权限、评测、A/B、多轮记忆或 Redis/Celery 基础设施。

实现参考：[SQLAlchemy Psycopg 支持](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg)、[pgvector Python ORM 集成](https://github.com/pgvector/pgvector-python#sqlalchemy)、[pgvector HNSW 与迭代扫描](https://github.com/pgvector/pgvector#iterative-index-scans)、[FastAPI 异常处理](https://fastapi.tiangolo.com/tutorial/handling-errors/)。
