# 验证记录

## 2026-11-08 GitHub CI

验证基线为 [9cc7201](https://github.com/Mengde-md/rag-center/commit/9cc72016b3e8ab792fca7bc4a85e265b4c476265)，对应的 [GitHub Actions 运行](https://github.com/Mengde-md/rag-center/actions/runs/42418976549)已通过。

- Python 3.11 下 Ruff 静态检查与格式检查通过，离线业务测试和 Day01 契约实验合计 **79 passed**。
- 集成任务使用 **PostgreSQL 16 + pgvector 0.8.1**，执行 **9 个真实数据库用例**并全部通过。每个用例单独创建 schema 并执行 Alembic 迁移，结束后清理自己的 schema。
- 集成验证覆盖向量排序、租户与知识库隔离、调用日志落库、写入失败回滚，以及模型后续批次失败时的 FAILED 状态与零残留分片。
- 模型请求由确定性向量或 HTTP MockTransport 替代，数据库迁移、写入、检索与事务操作使用真实 PostgreSQL。该记录对应上述提交；后续提交结果以对应 Actions 运行和 README 中的复现命令为准。

## 2026-10-21 初始本地验证

以下保留最初开发环境的验证记录。

### 已通过

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

### 当时的验证边界

- Compose 配置的目标是 **PostgreSQL 16 + pgvector 0.8.1**。本机 Docker Engine 未能启动，因此没有声称已完成镜像构建、容器启动或 PostgreSQL 16 运行验证。
- 未提供真实 Embedding API 凭据。测试中的模型响应使用确定性向量 / HTTP MockTransport；没有调用付费模型。生产代码使用 OpenAI-compatible HTTP Provider，运行前需要填写 `.env`。
- 当前 Starlette 的同步 TestClient 针对 httpx 发出一条弃用提示，38 个用例均通过；生产服务使用 httpx.AsyncClient。

实际部署请按 README 配置 `.env`，运行 `docker compose up --build -d`，再执行 README 中的三个接口示例验证真实模型链路。
