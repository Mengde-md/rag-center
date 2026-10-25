# RAG 中台交接与学习启动手册

版本 1.1　更新日期 2026-10-25　对应项目 rag-center 0.1.0

本手册用于接手和学习一个已经实现的 RAG 后端项目。接手者应能根据这里的路径找到真实源码，说明三个接口的调用链、数据库事务与失败边界，并按学习路线逐步独立复刻。技术栈已经由现有工程确定，本阶段不重新选框架，也不把未来扩展写成现有能力。

项目根目录为 `C:\path\to\rag-center`。下文代码链接均指向该目录内的真实文件。学习路线及学习状态统一维护在[学习路线总纲](RAG中台_学习路线总纲.md)，避免在多份文档中重复维护进度。

## 0 接手时先读什么

接手者先读本节、第 1 至 3 节以及学习总纲的当前进度，再阅读正在学习单元点名的源码和测试。只有遇到具体问题，才扩大到其他文件，不需要先读完所有历史对话和参考教材。

建议按以下顺序恢复事实：

1. 确认项目目录，阅读 [pyproject.toml](../../pyproject.toml)、[依赖锁](../../uv.lock) 和 [Compose 配置](../../docker-compose.yml)。
2. 阅读本手册中的能力边界、三条业务流程和验证边界。
3. 从总纲选取当前学习单元，打开对应生产源码和测试。
4. 执行 `git status --short` 识别已有改动；需要提交背景时再看 `git log --oneline -3`。没有提交历史时记录事实，不虚构版本提交点。
5. 判断本次任务是解释、编写教材、用户练习还是实现扩展，再执行与任务相关的检查。

2026-10-25 已核对 Git 根目录就是 `C:\path\to\rag-center`，当前工程基线提交为 `4b35219 feat: initialize RAG retrieval backend`。这只是本次交接快照，后续应重新执行 Git 命令确认，不能按旧对话猜测仓库边界。上层 ai 中的其他目录与用户文件不属于本学习任务；不要为了得到干净工作区而删除、覆盖或提交它们。

本次文档参考了用户提供的 CloudDrive 文档库的组织思路：问题驱动、源码走读、测试证据、失败复现和学习记录。这里不继承该项目的 Java 技术栈、固定天数、双仓库路径、自动提交要求或繁重的审批流程。

## 1 项目定位与交付范围

项目是面向业务系统的 RAG 检索能力服务。业务方负责提供租户、用户和问题；中台负责知识库、文档索引、向量召回及引用片段；业务方拿到这些片段后，可以自行调用生成模型。

当前业务闭环为：创建知识库 → 提交文本 → 同步索引 → 传入问题 → 返回结构化片段及引用元数据。返回内容不包含模型生成的答案。

| 状态 | 当前事实 |
| --- | --- |
| 已实现 | 三个 POST 业务接口、纯文本解析、字符切片、Embedding HTTP 调用、pgvector 检索、业务数据和成功检索日志落库 |
| 已实现 | 统一响应、参数校验、文档状态、失败事务回滚、租户与知识库过滤、数据库迁移、Provider 抽象 |
| 已预留 | 独立 IndexingService、EmbeddingProvider、VectorStore、DocumentParser、TextSplitter |
| 尚未实现 | 聊天界面、答案生成、PDF/Word 解析、BM25、rerank、任务队列、鉴权与 ACL、效果评测、反馈、Agent 工具循环 |
| 尚未证明 | 真实业务召回率、高并发容量、端到端延迟目标、成本下降、生产可用性 |

因此，当前可以称为“RAG 检索中台一期后端”或“工程化 RAG 服务 MVP”。自主规划、工具选择和执行反馈循环尚不存在，不应把它描述为已完成的 Agent 系统。

交接资料已建立，学习总纲现细化为 3 阶段、20 个核心学习日。当前启动第一阶段 Day01，相关教材、实验和学习状态从总纲进入；学习工作不新增业务接口，不重新选技术栈，也不替用户填写学习完成记录。

## 2 技术栈基线

### 2.1 已确定的技术选择

版本来自项目现有配置和锁文件，不代表这些软件的最新版本。后续安装以锁文件为准；如需升级，单独记录依赖差异并验证，不在学习过程中随意换版本。

| 层次 | 技术与版本基线 | 在项目中承担的职责 | 依据 |
| --- | --- | --- | --- |
| 语言 | Python 3.11，要求 `>=3.11,<3.12` | 类型标注、async/await、UUID、标准库 | pyproject.toml |
| HTTP 服务 | FastAPI 0.143.2 | 路由、依赖注入、请求与响应处理 | uv.lock |
| ASGI 服务器 | Uvicorn 0.54.0 | 接收 HTTP 请求并运行 FastAPI | uv.lock、app/__main__.py |
| 参数与配置 | Pydantic 2.14.1、pydantic-settings 2.16.0 | 请求校验、响应序列化、环境变量配置 | uv.lock、schemas、core/config.py |
| ORM | SQLAlchemy 2.0.54 | 数据模型、异步会话、SQL 表达式和事务 | uv.lock、db、repositories |
| 数据库驱动 | Psycopg 3.3.6，使用 binary 发行包 | PostgreSQL 的同步与异步连接 | uv.lock、postgresql+psycopg URL |
| 表结构管理 | Alembic 1.20.0 | 扩展、表、约束和索引的迁移 | uv.lock、migrations |
| 目标数据库 | PostgreSQL 16 | 知识库、文档、chunk、检索日志 | docker-compose.yml |
| 目标向量扩展 | pgvector 0.8.1 | vector 列、cosine 运算、HNSW 索引 | pgvector/pgvector:0.8.1-pg16 |
| Python 向量适配包 | pgvector 0.5.1 | SQLAlchemy VECTOR 类型与距离表达式 | uv.lock |
| 模型 HTTP 客户端 | httpx 0.28.1 | 调用 OpenAI-compatible `/embeddings` | uv.lock、providers/embedding |
| 测试 | pytest 9.1.1、pytest-asyncio 1.4.0 | 同步和异步测试 | uv.lock、tests |
| 静态检查 | Ruff 0.17.1 | 代码检查与格式校验 | uv.lock、pyproject.toml |
| 部署 | Dockerfile、Docker Compose | API 镜像、PostgreSQL、健康检查和数据卷 | 项目部署文件 |

注意三个版本概念：PostgreSQL 16 是数据库主版本；pgvector 0.8.1 是数据库扩展版本；pgvector 0.5.1 是 Python 包版本。不存在本项目采用了“pgvector 16”这一扩展版本的结论。

### 2.2 模型选择的确定程度

模型协议已经确定为 OpenAI-compatible Embedding HTTP API。生产代码通过 httpx 发送请求，没有引入 OpenAI SDK，也没有引入 LangChain 或 LlamaIndex。

`.env.example` 默认给出 `text-embedding-3-small`、1536 维和 OpenAI 基础 URL，它们是默认配置，不等于已有可用账号或已完成真实模型验收。可以替换为兼容该请求和响应协议的服务，但必须核对原生输出维度及语义空间。

当前请求发送 `model`、`input`、`encoding_format=float`，不发送 `dimensions` 参数。因此，设置 EMBEDDING_DIMENSIONS 只影响本地校验和建库维度，不能强迫上游模型缩短输出。

### 2.3 配置与依赖的事实来源

- [pyproject.toml](../../pyproject.toml) 记录依赖范围与 Python 约束。
- [uv.lock](../../uv.lock) 锁定运行和开发依赖；[requirements.lock](../../requirements.lock) 是固定生产依赖的导出文件，Docker 使用它安装。
- [.env.example](../../.env.example) 给出安全的配置样例；真实密钥只保留在本地环境或受控配置中。
- [Settings](../../app/core/config.py) 决定配置字段、默认值和校验规则。环境变量优先于 `.env`；默认 `.env` 路径相对于当前工作目录。
- `get_settings()` 有进程内缓存。修改 `.env` 后应重启进程；不要期待已创建的模型、连接池或 Provider 自动更新。

## 3 当前验证状态怎样理解

### 3.1 历史验证事实

[VERIFICATION.md](../../VERIFICATION.md) 记录了 2026-10-21 的运行结果：Python 3.11.4，38 项测试通过，其中 31 项为单元或契约用例、7 项为真实数据库集成用例；真实数据库环境是 PostgreSQL 17.11 与 pgvector 0.8.6。Alembic 升级、回退、结构一致性检查和 Windows 真实 HTTP 冒烟也曾通过。

这份记录同时说明：当时未能启动 Docker Engine，没有运行 PostgreSQL 16 目标容器；未提供真实 Embedding 密钥，模型响应由确定性向量或 MockTransport 替换。历史记录不能写成目标生产组合已经验收。

### 3.2 本次文档核对与未来验收

本次核对依据现有源码、锁文件、接口契约和测试文件；机器可读结果见[基线核对记录](基线核对记录_2026-10-25.json)。本次执行的检查与历史检查在记录中分开存放。

| 2026-10-25 交接资料制作时的检查 | 结果与边界 |
| --- | --- |
| 单元与接口契约测试 | 31 passed、7 deselected，保留 1 条 Starlette TestClient 弃用提示；未执行数据库集成 |
| Ruff 检查与格式检查 | 均通过 |
| Docker Compose 配置解析 | 通过；没有启动或验证容器 |
| 文档交叉核对 | 107 个相对链接存在，22 个测试函数名可定位，12 个单元编号连续 |
| 真实数据库与真实模型调用 | 本次未执行，继续保留历史环境和目标组合的区别 |

上表及基线 JSON 保留首次交接时的快照，不负责维护后续学习进度。Day01 的独立检查结果见[本日验收记录](../学习单元/第一阶段/Day01_实验/验收记录.json)；是否已完成用户学习仍只看总纲及用户记录。

之后复验必须记录日期、Python 与数据库版本、命令、退出状态、通过和跳过数量、是否替换了模型。没有运行的检查应写“未运行”，不能把 Docker 配置校验当作容器已启动，也不能把 Mock 测试当作真实模型调用成功。

三类结论应分开表达：代码行为通过测试、教材解释已核对、用户已掌握。前两类可以由 AI 提供证据；最后一类需要用户自己解释和操作，不能由测试数量替代。

## 4 源码地图与阅读顺序

### 4.1 分层责任

```mermaid
flowchart TD
    Caller[业务调用方] --> API[API 路由与 Pydantic Schema]
    API --> Service[业务 Service]
    Service --> Repo[Repository]
    Repo --> PG[(PostgreSQL)]
    Service --> Indexing[IndexingService]
    Indexing --> Parser[DocumentParser 与 TextSplitter]
    Indexing --> Embedding[EmbeddingProvider]
    Service --> Embedding
    Embedding --> Model[兼容协议的 Embedding 服务]
    Indexing --> Vector[VectorStore]
    Service --> Vector
    Vector --> ChunkRepo[PgVectorStore 与 ChunkRepository]
    ChunkRepo --> PG
```

API 路由负责 HTTP 入参和出参。Service 决定业务顺序及事务边界。Repository 执行数据库读写，使用 flush 而不替业务自行 commit。Provider 将外部能力包装成稳定接口。SQLAlchemy 会话的 commit、rollback 位于 Service 中是当前实现的选择，并不意味着 Service 内直接编写检索 SQL。

### 4.2 按问题找文件

| 要回答的问题 | 生产源码入口 | 对应测试 |
| --- | --- | --- |
| 服务如何启动、如何释放资源 | [启动入口](../../app/__main__.py)、[应用工厂](../../app/main.py)、[会话与维度检查](../../app/db/session.py) | test_real_lifespan_and_openai_provider_through_all_three_routes |
| 依赖是怎样装配的 | [dependencies.py](../../app/api/dependencies.py) | 集成测试的 session 与 embedding overrides |
| 创建知识库如何持久化 | [KnowledgeBaseService](../../app/services/knowledge_base_service.py)、[KnowledgeBaseRepository](../../app/repositories/knowledge_base_repository.py) | test_create_upload_retrieve_and_persist_log |
| 文本如何变成 chunk | [PlainTextParser](../../app/providers/parsers/plain_text.py)、[TextSplitter](../../app/utils/text_splitter.py) | tests/test_text_processing.py |
| 模型返回错序或坏向量怎么办 | [Embedding Provider](../../app/providers/embedding/openai_compatible.py) | tests/test_embedding_provider.py |
| 文档上传的事务如何划分 | [DocumentService](../../app/services/document_service.py)、[IndexingService](../../app/services/indexing_service.py)、[DocumentRepository](../../app/repositories/document_repository.py) | 两个失败恢复用例、test_multichunk_indexing_and_top_k_limit |
| 检索如何过滤并排序 | [RagService](../../app/services/rag_service.py)、[ChunkRepository](../../app/repositories/chunk_repository.py) | test_tenant_and_knowledge_base_isolation、test_create_upload_retrieve_and_persist_log |
| 错误如何变成统一响应 | [异常处理](../../app/core/exceptions.py)、[公共 Schema](../../app/schemas/common.py) | tests/test_api_contract.py |
| 表、外键和向量索引在哪里 | [四个模型](../../app/models/__init__.py)、[初始迁移](../../migrations/versions/0001_initial.py) | tests/test_integration.py 的真实迁移和数据断言 |

完整测试文件入口为 [API 契约](../../tests/test_api_contract.py)、[配置](../../tests/test_config.py)、[文本处理](../../tests/test_text_processing.py)、[模型协议](../../tests/test_embedding_provider.py)、[数据库集成](../../tests/test_integration.py)。测试名称也是后续教材的定位锚点，不要凭印象创建一个不存在的测试名。

## 5 三个接口的真实契约

业务接口只有三个，均为 POST。`/docs`、`/redoc`、`/openapi.json` 是文档设施，不是额外业务能力。

| 接口 | 必要输入 | 成功输出要点 |
| --- | --- | --- |
| `/api/v1/knowledge-bases/create` | tenant_id、name；description 可选 | kb_id、name、tenant_id、created_at |
| `/api/v1/documents/upload` | tenant_id、kb_id、title、content | document_id、kb_id、整数 status、chunk_count |
| `/api/v1/rag/retrieve` | tenant_id、kb_id、user_id、query | query、kb_id、retrieved_chunks、metadata |

输入和输出的详细定义见 [KnowledgeBase Schema](../../app/schemas/knowledge_base.py)、[Document Schema](../../app/schemas/document.py)、[RAG Schema](../../app/schemas/rag.py)。请求模型禁止额外字段；例如在当前检索请求中增加 `top_k` 会触发 422，TOP_K 当前是服务配置，不是单次请求参数。

统一响应结构为：

```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

`code=0` 表示成功，错误使用非零业务码，同时保留 404、413、422、500、502 等 HTTP 状态。只有格式正确的 JSON 还不够，调用方仍应先判断 HTTP 状态和 code，再使用 data。

外部业务方提供 tenant_id 与 user_id；内部 kb_id、document_id、chunk_id、retrieval_log_id 通过 [generate_id](../../app/utils/id_generator.py) 统一生成 UUID。真正请求必须使用 UUID，需求说明中的 `kb_xxx` 只是一种示意，不能直接发送给当前接口。

## 6 创建知识库的执行过程

路由接收 KnowledgeBaseCreate 后调用 KnowledgeBaseService.create。Repository 构造 ORM 对象并 flush，数据库返回 ID 和创建时间，Service commit 后组装 KnowledgeBaseCreated。

这里的 flush 会把 SQL 送到数据库，但不会替当前事务做最终提交。若后续步骤失败，在提交前仍可以回滚；只有 commit 成功后，才形成该请求持久化完成的结果。

当前不要求同一租户内知识库名称唯一，也没有列出、删除或修改知识库的业务接口。不要在教材示例中假设这些功能存在。

## 7 上传文档的执行过程与事务

### 7.1 正常路径

```mermaid
sequenceDiagram
    participant C as 调用方
    participant D as DocumentService
    participant DB as PostgreSQL
    participant I as IndexingService
    participant E as EmbeddingProvider
    C->>D: tenant_id kb_id title content
    D->>D: 检查长度与知识库归属
    D->>DB: 创建 PROCESSING 文档并提交
    D->>I: index_document
    I->>I: 解析 规范化 切片
    I->>E: embed_texts 分批请求
    E-->>I: 向量列表
    I->>DB: 经 VectorStore 写入 chunks 并 flush
    I-->>D: chunk_count
    D->>DB: 设置 SUCCESS 并提交同一事务
    D-->>C: document_id status 1 chunk_count
```

第一段事务创建 PROCESSING 文档并提交，使后续外部模型调用失败时仍有可追踪记录。第二段事务包含 pgvector chunk 写入和 SUCCESS 状态更新，两者使用同一 SQLAlchemy Session，提交时一起生效。

虽然方法使用 `async def`，上传请求仍等待解析、Embedding 和索引全部结束后才响应。这是同步完成业务流程，async/await 只表示等待 I/O 的执行方式，不代表已经有后台任务队列。

### 7.2 失败路径

| 失败位置 | 当前响应与数据库结果 |
| --- | --- |
| 请求字段不合法、纯空白内容 | 422，尚未创建文档 |
| content 超过 MAX_CONTENT_LENGTH | 413，尚未创建文档 |
| 知识库不存在或 tenant_id 不匹配 | 404 与 40001，尚未创建文档 |
| 创建文档阶段数据库故障 | 通用 500；不能保证文档已经持久化 |
| Embedding 配置、超时或响应校验失败 | 回滚 chunk 事务，独立保存 FAILED 与 error_message，HTTP 502、业务码 50202 |
| 其他解析、切片或向量写入错误 | 回滚 chunk 事务，独立保存 FAILED，HTTP 500、业务码 50002 |
| 故障期间数据库也不可写 | 无法保证 FAILED 状态立即落库，应查数据库和应用记录 |

状态枚举固定为 `1=SUCCESS`、`2=FAILED`、`3=PROCESSING`。失败响应中的 document_id 用于定位真实记录，不能把请求失败等同于数据库什么都没写。

两个重要边界需要保留：进程被强制终止可能留下 PROCESSING；当前没有自动重试、任务补偿或幂等键，重传相同文本会新建文档。数据库提交结果不明等断连场景也没有经过专项故障验证，不能由正常回滚测试外推为任意故障下都能自动恢复。

### 7.3 IndexingService 负责什么

IndexingService 接收 document_id、tenant_id、kb_id、title、content，依次调用 DocumentParser、TextSplitter、EmbeddingProvider 和 VectorStore。它生成 chunk UUID，将文本与向量、标题、租户归属、切片位置组合成 IndexedChunk，最后返回写入数量。

它不处理 HTTP，不自行 commit，也不负责决定上传失败的响应码。未来把索引迁入任务系统时可以复用这一业务入口，但还需要补充任务持久化、幂等、重试、超时恢复和外部写入补偿，不能只把方法丢进后台就称为完整异步方案。

## 8 文本解析和切片的具体含义

PlainTextParser 只接收字符串，将 CRLF/CR 规范为 LF，去掉开头的 BOM，并拒绝没有可索引字符的结果。Markdown 按文本保留，不生成标题树或页码。当前 API 不接收 multipart 文件流，调用方应先读取 `.txt` 或 `.md`，再把文本放入 content。

CharacterTextSplitter 使用 Unicode 字符窗口，默认 CHUNK_SIZE=800、CHUNK_OVERLAP=100。窗口从 0 开始，每轮末尾位置为 `min(start+size, 文本长度)`，下轮起点为 `end-overlap`。末尾已到全文末端时退出，纯空白窗口会被跳过。

例如大小为 8、重叠为 2 时，窗口起点通常是 0、6、12。这里按 Python 字符位置计数，不是按模型 token 数，也没有承诺在句子或段落边界切断。

chunk 的 start_char 与 end_char 是**规范化文本**的左闭右开位置，可以用 `text[start_char:end_char]` 取出同一片段；它们不是原始上传文件的字节偏移、PDF 页码或浏览器字符位置。chunk_index 对应保留后的片段序号。

## 9 Embedding 调用的具体含义

EmbeddingProvider 抽象定义 embed_texts，embed_query 默认复用单条文本的向量生成。OpenAICompatibleEmbeddingProvider 使用共享的 httpx.AsyncClient，将基础 URL 后追加 `/embeddings`，把密钥放入 Authorization 头。

当前实现按 EMBEDDING_BATCH_SIZE 切批，批次逐个 await，不是同时发出全部批次。对每批响应执行以下检查：

1. HTTP 状态成功，响应可解析为约定结构。
2. 按响应 index 排序，索引集合必须恰好对应本批输入位置。
3. 每个向量长度等于 EMBEDDING_DIMENSIONS。
4. 每个值为有限数，向量不能全为零。

异常会转换为安全的 EmbeddingError，避免把上游原始响应或密钥送回调用方。当前没有自动重试、速率限制、向量缓存或模型回退。更换同维度模型同样可能改变语义空间，文档向量和 query 向量不能混用两个模型的空间。

## 10 检索与日志的执行过程

RagService 先生成 retrieval_log_id，确认 tenant_id 与 kb_id 能访问到同一知识库，再 rollback 结束只读事务，把连接交还连接池后调用模型。这里的 rollback 不是业务失败，而是主动结束一次不需要提交的只读查询事务。

随后调用 VectorStore.similarity_search。当前 PgVectorStore 把调用委托给 ChunkRepository，它按 tenant_id、kb_id 和 Document.status=SUCCESS 过滤，计算 cosine distance，按距离升序取前 TOP_K 条；返回分数为 `1-distance`，并钳制到 [-1,1]。

数据库已创建 HNSW cosine 索引，查询启用 `hnsw.iterative_scan=strict_order` 以改善过滤后的扫描。HNSW 属于近似检索；是否实际走索引由执行计划决定，小数据测试通过不能证明大数据时的召回率或索引收益。高相关分数也不是答案正确的概率。

结果包含文档 ID、chunk ID、标题、片段原文、分数与切片元数据；外层 metadata 包含 top_k、vector_store 和 retrieval_log_id。当前不返回 context_text，不做模板拼接，不调用生成模型，也没有 query 改写和 rerank。

RagService 将成功召回结果写入 RetrievalLog，再 commit 后返回。日志中的 latency_ms 在日志写入前计算，因此不包含日志 flush/commit 和最终 HTTP 序列化等全部耗时；不要把它直接当作完整请求的端到端延迟。失败检索目前没有对应的业务失败日志表记录；日志写入本身失败也会使该次请求失败，而不是静默降级。

## 11 数据模型和数据库约束

```mermaid
erDiagram
    KNOWLEDGE_BASES ||--o{ DOCUMENTS : contains
    DOCUMENTS ||--o{ CHUNKS : contains
    KNOWLEDGE_BASES ||--o{ RETRIEVAL_LOGS : records
```

| 表 | 主要字段 | 需要理解的设计 |
| --- | --- | --- |
| knowledge_bases | id、tenant_id、name、description、created_at、updated_at | tenant_id 与 id 组合唯一，支撑归属外键 |
| documents | id、tenant_id、kb_id、title、source_type、status、chunk_count、error_message、时间 | 复合外键绑定知识库租户；status 限定 1/2/3，chunk_count 非负 |
| chunks | id、tenant_id、kb_id、document_id、title、content、metadata、embedding、created_at | 复合外键绑定文档、知识库和租户；vector 列与 HNSW 索引 |
| retrieval_logs | id、tenant_id、kb_id、user_id、query、retrieved_chunks、top_k、vector_store、latency_ms、created_at | 记录成功检索的输入、结果快照与元信息 |

业务层的 tenant_id 条件和数据库复合外键解决不同问题：前者限制查询范围，后者防止错误写入跨租户、跨知识库的关系。两者都没有验证请求者真实身份；调用方仍能自行填写 tenant_id，因此它们不能替代认证和 ACL。

Chunk 在 Python 中使用 chunk_metadata 属性，数据库物理列仍叫 metadata，这是为了避开 SQLAlchemy DeclarativeBase.metadata 的保留属性。教材应区分 ORM 属性名和数据库列名。

Document 当前不保存完整原始 content，也不保存原文件；原文片段保存在 chunks 中，且已经规范化、切片。失败文档可能没有任何 chunk。未来要支持重新解析、重试或完整重建，需另外设计原始资料保留或由调用方重新提供内容。

## 12 统一错误与资源生命周期

### 12.1 错误码需要按调用位置解释

| HTTP | code | 含义 |
| --- | --- | --- |
| 404 | 40001 | 知识库不存在或租户不匹配 |
| 413 | 41301 | 上传内容超过字符数上限 |
| 422 | 42201 | 请求 Schema 校验失败 |
| 502 | 50201 | 检索等调用中直接暴露的 EmbeddingError |
| 502 | 50202 | 上传流程捕获 EmbeddingError，并已尝试保存 FAILED |
| 500 | 50002 | 上传索引的其他错误，并已尝试保存 FAILED |
| 500 | 50000 | 未处理的内部错误 |
| 404 / 405 | 40400 / 40500 | 框架路径不存在或 HTTP 方法不匹配 |

校验错误只返回 loc、msg、type，不回传输入文档全文。非预期错误返回通用信息；现有日志策略不输出完整 SQL 参数、上游密钥或原始错误体。

### 12.2 生命周期和会话归属

FastAPI lifespan 创建异步引擎和 session_factory，验证 chunks.embedding 的数据库维度，创建共享 AsyncClient 与 Embedding Provider。退出时关闭 HTTP 客户端并 dispose 数据库引擎。

get_session 为每个请求提供会话，结束时 rollback 清理未完成事务。Service 的成功与失败分支决定 commit 的位置。Dependencies 是装配具体 PgVectorStore、Repository、Parser、Splitter 的入口，Service 依赖 Provider 抽象。

启动检查只验证既有向量列是否存在、维度是否一致，不会替你 create_all，也不等于检查了全部表、索引、权限和数据质量。迁移必须在启动前完成。

## 13 本地运行和复验

本节是接手时可执行的最小流程。以下命令以 PowerShell 为例，先进入项目根目录；运行前确认现有 `.env` 和数据库，保留用户配置。

```powershell
Set-Location -LiteralPath 'C:\path\to\rag-center'
& '.\.venv\Scripts\python.exe' --version
```

### 13.1 不依赖数据库与模型的检查

已有项目虚拟环境时可直接运行：

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -m 'not integration' -q
& '.\.venv\Scripts\ruff.exe' check .
& '.\.venv\Scripts\ruff.exe' format --check .
```

缺少环境时使用 Python 3.11 建立虚拟环境，先装固定生产依赖，再安装项目与开发依赖：

```powershell
py -3.11 -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.lock
& '.\.venv\Scripts\python.exe' -m pip install -e '.[dev]'
```

已安装 uv 时可用 `uv sync --locked --extra dev --python 3.11` 同时锁定运行与开发依赖。若系统的 py 启动器没有注册解释器，应使用一个已核验为 3.11 的真实 Python 路径，不把 WindowsApps 占位程序当作解释器。

### 13.2 目标 Docker 组合

```powershell
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
# 编辑 .env 中的模型地址、密钥、模型名及原生输出维度
docker info
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs api
```

Compose 等待 PostgreSQL 健康后启动 API，API 镜像命令先执行 Alembic upgrade，再执行 python -m app。默认宿主机端口为数据库 5432、API 8000，均绑定本机回环地址；容器内 API 监听 0.0.0.0。健康检查访问 OpenAPI，不验证真实 Embedding 能否成功。

缺少模型密钥时服务和创建知识库可以启动，文档上传与检索会明确失败。不要为了演示成功，在生产 Provider 中悄悄改用固定向量。

### 13.3 本机 Python 加数据库

先启动 PostgreSQL 并核对连接串，然后执行：

```powershell
& '.\.venv\Scripts\python.exe' -m alembic upgrade head
& '.\.venv\Scripts\python.exe' -m alembic check
& '.\.venv\Scripts\python.exe' -m app
```

Windows 推荐使用项目的 python -m app 入口，它在创建事件循环时显式选择 Selector，适配 Psycopg 异步连接。容器启动也走同一入口。可通过 `--host` 与 `--port` 修改监听地址和端口。

### 13.4 三个请求的手工闭环

```powershell
$base = 'http://localhost:8000/api/v1'
$kb = Invoke-RestMethod -Method Post -Uri "$base/knowledge-bases/create" `
    -ContentType 'application/json; charset=utf-8' `
    -Body (@{name='学习知识库'; tenant_id='tenant_demo'} | ConvertTo-Json)
$kbId = $kb.data.kb_id

$upload = Invoke-RestMethod -Method Post -Uri "$base/documents/upload" `
    -ContentType 'application/json; charset=utf-8' `
    -Body (@{tenant_id='tenant_demo'; kb_id=$kbId; title='退款规则'; content='用户可在订单完成后七天内申请退款。'} | ConvertTo-Json)
$upload | ConvertTo-Json -Depth 8

$result = Invoke-RestMethod -Method Post -Uri "$base/rag/retrieve" `
    -ContentType 'application/json; charset=utf-8' `
    -Body (@{tenant_id='tenant_demo'; kb_id=$kbId; user_id='user_demo'; query='退款申请期限是多少？'} | ConvertTo-Json)
$result | ConvertTo-Json -Depth 12
```

验收时记录 kb_id、document_id、chunk_count、retrieval_log_id、召回片段和时间。真实模型可能存在网络或限流错误，失败也应记录 HTTP 状态、业务码和数据库状态，不要只保留成功截图。

### 13.5 真实数据库测试

集成测试要求数据库名以 `_test` 结尾，每个测试创建独立 schema 并在结束后删除自己的 schema。数据库账号还需要建 schema 和安装或使用 vector 扩展的权限。

```powershell
docker compose exec postgres createdb -U postgres rag_center_test
$env:TEST_DATABASE_URL = 'postgresql+psycopg://postgres:postgres@localhost:5432/rag_center_test'
& '.\.venv\Scripts\python.exe' -m pytest -q
```

若测试库已经存在，不要重复创建或擅自删除；核对后复用专用测试库即可。不要把业务库改名伪装成测试库。未设置 TEST_DATABASE_URL 时，集成用例会 skipped，这不等于集成通过。

## 14 配置中的学习重点

| 配置项 | 默认值 | 应理解的问题 |
| --- | --- | --- |
| DATABASE_URL | postgresql+psycopg 指向本机 rag_center | 宿主机与容器内的数据库地址不同 |
| EMBEDDING_MODEL / DIMENSIONS | text-embedding-3-small / 1536 | 模型空间和数据库维度必须匹配 |
| EMBEDDING_BATCH_SIZE | 32 | 分批减少单次请求大小，但当前批次串行 |
| MODEL_TIMEOUT_SECONDS | 60 | 是 HTTP 客户端超时设置，不是整个上传流程的统一总时限 |
| CHUNK_SIZE / OVERLAP | 800 / 100 | overlap 必须小于 size，单位是字符 |
| TOP_K | 5 | 最大候选数量，不保证一定有 5 条结果 |
| MAX_CONTENT_LENGTH | 100000 | 单次内容字符上限，不是字节数或完整反向代理请求体限制 |
| VECTOR_STORE | pgvector | 当前只接受这个实现名，新增实现需要改装配和配置校验 |

EMBEDDING_DIMENSIONS 首次建库时决定 vector 列和索引维度，当前限制 1–2000。修改已有数据库维度需要新迁移与重新索引；不能只改 `.env` 后继续使用旧数据。

## 15 测试证据与不能外推的结论

| 测试文件 | 关键证明 | 不能据此证明 |
| --- | --- | --- |
| test_api_contract.py | 恰好三个业务路由、统一响应、参数和异常序列化 | 数据库可连接；该文件刻意不启动 lifespan |
| test_config.py | 非法配置提前失败 | 所有有效配置都对应可用外部服务 |
| test_text_processing.py | Unicode 位置、窗口重叠、边界、空白、文本规范化 | 领域语义完整性或 PDF 解析质量 |
| test_embedding_provider.py | HTTP 请求格式、批次顺序、坏向量、超时与错误脱敏 | 当前真实账号可用、真实模型语义效果 |
| test_integration.py | 真迁移、持久化、排序、过滤、日志、回滚、lifespan | 真实模型质量、PG16 容器已运行、生产负载下性能 |

集成用例中的两个失败恢复测试分别模拟 Embedding 故障，以及 chunk 实际 INSERT 后触发 SQL 错误。后一种情况使真实事务进入失败状态，再验证 rollback 与独立保存 FAILED，因此比单纯在调用前抛异常多覆盖一层数据库行为。

集成测试还显式指定每个 schema 内的 Alembic 版本表，避免 public.alembic_version 使新 schema 被误判为已经迁移。固定测试向量只用于受控排序和工程行为验证，不能拿它计算真实业务的 Recall 或答案正确率。

## 16 常见故障的排查顺序

| 现象 | 先核对什么 | 当前能得出的结论 |
| --- | --- | --- |
| python 命令无法启动 | 项目 .venv 的真实解释器、Python 版本 | 解释器路径问题不等于中文目录不受支持 |
| 启动提示 Database schema missing | DATABASE_URL 与 Alembic 是否在同一库执行 | 缺迁移或连接错库，不应由应用偷偷建表 |
| 维度不一致而拒绝启动 | 模型原生维度、配置、数据库 vector 列 | 不能通过跳过校验继续混用 |
| 上传返回 50202 | MODEL_API_KEY、基础 URL、上游 HTTP 状态、超时、FAILED 文档 | 请求失败后可能已有文档记录 |
| 相同内容重复出现 | 调用方重传、知识库内已有文档、当前没有幂等 | 不能归因于向量索引自动去重失败 |
| 检索没有结果 | kb_id 与 tenant_id、文档状态、chunk 数量、模型空间 | 空结果不直接证明模型故障 |
| 测试全绿但 7 项 skipped | TEST_DATABASE_URL 与测试摘要 | 只完成了不依赖数据库的部分 |
| Docker 客户端存在但启动失败 | docker info、Engine、Compose 输出 | 命令存在不等于引擎或容器可用 |
| 错误响应没有内部堆栈 | 统一异常策略、业务码与服务日志 | 脱敏设计不代表没有异常，需要保留可定位证据 |

排查时先核对命令的工作目录、实际配置和返回状态，再讨论是否是环境限制。不要为消除一次错误就删除数据卷、重建业务库、覆盖密钥文件或修改全局系统配置。

## 17 后续教材怎样编写

完整要求见[学习路线总纲](RAG中台_学习路线总纲.md)。每个单元必须从真实项目问题出发，连接概念、生产源码、测试断言、一次可复现失败和独立练习。源码中的关键方法应逐段解释，引用测试时要说明输入、断言和证据边界。

现有项目已经完成一期实现，后续教材应写“为什么这样实现、如何验证、怎样自己复刻”。不要假装代码尚不存在，也不要让用户在正式项目中先删掉后续类、表或依赖来配合教学进度。练习可以使用用户指定的练习副本或独立小实验；尚未指定练习路径时，先做不修改代码的走读和设计练习。

不以 800 行、多少页或多少段代码作为教材通过条件。完整性由问题、机制、真实实现、测试、失败复现和学习产物决定；避免把同一段代码在多份教材中反复粘贴。

## 18 下一位接手者的任务模板

下面的模板用于继续编写某个学习单元，不自动授权发布、合并、改动其他项目或对外发送消息。

```text
项目：C:\path\to\rag-center
交接入口：docs\交接文档及学习路线\RAG中台_交接与学习启动手册.md
范围来源：同目录的 RAG中台_学习路线总纲.md

先读取当前进度和本次选定单元，核对该单元的源码、测试、现有教材与工作区改动。
本次目标：完成用户选定 Day 的完整学习教材，并核对它对应的 U 单元范围。
交付应包含：真实问题、概念推导、生产源码走读、测试矩阵、运行步骤、失败复现、练习、面试解释和验收清单。
本次未授权的功能扩展不实现；不更换技术栈；不删除现有源码来模拟从零开发。
有运行的检查给出日期、环境、命令和结果；没运行的明确说明，不复制历史结果充当本次结果。
工程行为、教材质量、用户学习状态分别记录，用户学习完成记录不能由 AI 代填。
```

## 19 可讲述的成果和后续方向

当前可以围绕 Provider 抽象、同步索引的事务边界、租户归属约束、参数和错误协议、模型响应校验、HNSW cosine 检索、迁移及故障测试进行项目讲解。每项讲述都应能回到一个真实方法和测试，而不是只罗列技术名词。

后续扩展候选包括 BM25 混合检索、rerank、异步任务、其他向量库、身份认证和 ACL、评测集与反馈、管理后台。它们只作为候选，不属于当前 12 个基线学习单元的实现要求。尤其在补充真实问题集与对照实验前，不应宣称召回率提升、幻觉下降或成本降低的具体数值。

完成这套基线学习后，用户应能独立解释“请求为什么经过这些层、每次提交改变了什么、失败后数据库会留下什么、测试证明到哪里”。这也是进入检索效果优化与真实业务扩展前应具备的基础。
