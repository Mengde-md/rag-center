# 验证记录

验证日期：2026-10-21。

## 已通过

- Python 3.11.4：完整测试集 **38 passed**，包括 31 个单元/契约用例和 7 个真实数据库集成用例。
- 真实测试数据库：本机独立临时 PostgreSQL **17.11** + pgvector **0.8.6**，每个集成用例使用独立 schema。
- 创建知识库 → 同步文档切片、Embedding、向量写入 → cosine 检索、引用元数据、调用日志落库。
- 多切片与 TOP_K 上限，tenant_id / kb_id 过滤。
- Embedding 故障后 FAILED 状态持久化；实际 INSERT 后故意触发 SQL 错误，验证 chunk 回滚与失败状态的独立事务。
- FastAPI lifespan、数据库维度检查、真实 OpenAI-compatible Provider（测试 HTTP 响应）与三个路由组合运行。
- Alembic `upgrade head` → `check` → `downgrade base` → `upgrade head` → `check`，未发现 ORM / 数据库结构差异。
- 在 public 已存在迁移版本和业务数据的测试库中，再次运行全部测试通过；各用例的 Alembic 版本表与业务表均限定在自己的临时 schema 中。
- Ruff 静态检查与格式检查、Python 编译检查、`docker compose config --quiet`。
- Windows 上以 `python -m app --host 127.0.0.1 --port 58000` 启动真实 Uvicorn，访问 OpenAPI 并通过 HTTP 成功创建知识库；测试进程随后关闭。

## 验证边界

- Compose 配置的目标是 **PostgreSQL 16 + pgvector 0.8.1**。本机 Docker Engine 未能启动，因此没有声称已完成镜像构建、容器启动或 PostgreSQL 16 运行验证。
- 未提供真实 Embedding API 凭据。测试中的模型响应使用确定性向量 / HTTP MockTransport；没有调用付费模型。生产代码使用 OpenAI-compatible HTTP Provider，运行前需要填写 `.env`。
- 当前 Starlette 的同步 TestClient 针对 httpx 发出一条弃用提示，38 个用例均通过；生产服务使用 httpx.AsyncClient。

实际部署请按 README 配置 `.env`，运行 `docker compose up --build -d`，再执行 README 中的三个接口示例验证真实模型链路。
