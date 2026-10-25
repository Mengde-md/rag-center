# RAG 中台学习路线总纲

版本 1.1　更新日期 2026-10-25　适用项目 rag-center 0.1.0

本路线用于学习已经实现的 RAG 检索中台一期。学习者从真实源码和已有测试出发，逐步理解、运行、解释并独立复刻项目；不要求先清空工程重新开发。技术栈已由现有工程确定，详细版本及能力边界见[交接手册](RAG中台_交接与学习启动手册.md)。

12 个单元保留为知识主题，本版进一步拆成 20 个核心学习日。默认每天 2–3 小时，约 4 周完成，每周另外留出 1 天复盘和 1 天机动。Day 是能力验收单元，遇到基础薄弱或外部环境未就绪时可以延长，不以日历到期强行标记完成。

## 1 学完以后应具备什么能力

学习者应能够独立画出三个请求的执行链，解释 Pydantic、依赖注入、Service、Repository、Provider 和 PostgreSQL 分别承担什么责任；能够说明 flush、commit、rollback 在文档成功与失败路径中改变了什么；能够运行测试并指出其证明范围。

此外，应能自己实现一个字符切片器，用受控 HTTP 响应测试 Embedding 协议，写出带 tenant_id 与 kb_id 条件的检索查询，识别真实模型、数据库版本、部署和评测仍未验收的部分。面试讲述应落实到具体代码、约束、失败和证据，不虚构线上规模或收益。

## 2 学习前的准备

建议先确认自己能阅读 Python 函数、类、列表、字典和异常处理。对类型标注、dataclass、UUID、async/await 不熟悉时，可以在单元中补充对应的小实验，不需要先学完所有 Python 知识。

第一轮学习先以正式项目为只读参照。闭卷复刻使用用户指定的练习目录或独立实验文件，不为了配合章节顺序改坏正式项目，也不把练习目录默认设为参考 CloudDrive 的任何仓库。练习路径一旦确定，在本文件的学习记录中记录一次即可。

项目根目录是 `C:\path\to\rag-center`。完整教材放在 `docs/学习单元/阶段目录/` 下，按 Day 与主题命名。当前从[第一阶段 Day01](../学习单元/第一阶段/RAG中台_Day01_项目边界工程入口与契约验证.md)开始；用户学习状态仍由用户自己的练习与解释确定。

## 3 总体安排

| 阶段 | 单元 | 学习主题 | 本阶段可检查的产物 |
| --- | --- | --- | --- |
| 第一阶段 Day01–05 | U01–U03 | 项目定位、Python 数据契约、FastAPI 装配与生命周期 | 项目地图、请求校验说明、依赖和资源图 |
| 第二阶段 Day06–14 | U04–U08 | 数据模型、迁移、知识库、文本切片、Embedding、索引事务 | 表关系图、切片复刻、协议测试、事务时间线 |
| 第三阶段 Day15–20 | U09–U12 | 向量召回、错误日志、测试隔离、部署与项目讲述 | 检索 SQL 解释、失败矩阵、复验记录、项目讲解稿 |

每个单元都包含一个可观察的问题、一组真实生产源码、一组测试、一个独立练习和清晰的完成标准。已有实现会跨单元被解释，但后面的知识只做必要提示，不在前面重复展开全部内容。

### 3.1 周期与时间投入

20 个核心学习日约需 40–60 小时，复盘和机动时间另计。按每周 5 个核心学习日安排，四周覆盖整个基线。若每天只能投入 1 小时，可把每个 Day 拆成 2–3 次；按每周 5 次计算约需 8–12 周，学习内容和验收标准不因此减少。

| 周次 | 核心学习日 | 本周目标 | 周末建议 |
| --- | --- | --- | --- |
| 第 1 周 | Day01–05 | 看懂工程、数据契约与请求装配 | 1 天闭卷复盘，1 天机动 |
| 第 2 周 | Day06–10 | 理解数据约束、事务、切片和模型协议 | 复盘 ER 图、SQL 与字符切片 |
| 第 3 周 | Day11–15 | 贯通模型容错、同步索引与向量召回 | 重画失败事务和过滤查询 |
| 第 4 周 | Day16–20 | 理解检索日志、测试隔离并完成复验讲述 | 整理证据和未完成项 |

### 3.2 每个 Day 的范围

| Day | 阶段与主题 | 对应单元 | 当天可检查的学习产物 |
| --- | --- | --- | --- |
| Day01 | 第一阶段 项目边界与工程入口 | U01 | 三接口地图、启动链、OpenAPI 契约检查 |
| Day02 | Python 类型、UUID、枚举与数据类 | U02 前半 | 内部对象与外部字段对照、小型建模练习 |
| Day03 | Pydantic 请求与响应契约 | U02 后半 | 合法与非法输入矩阵、序列化解释 |
| Day04 | 配置、依赖注入与 lifespan | U03 | 配置来源图、会话和客户端生命周期图 |
| Day05 | 第一阶段整合复盘 | U01–U03 | 闭卷解释请求装配，复刻最小契约检查 |
| Day06 | 四张表与复合外键 | U04 前半 | ER 图、租户归属约束与 SQL 练习 |
| Day07 | Alembic 与向量列迁移 | U04 后半 | 迁移 SQL、测试库升级与结构检查记录 |
| Day08 | 创建知识库与基础事务 | U05 | flush、commit、rollback 的观察记录 |
| Day09 | 文本规范化与字符切片 | U06 | 独立切片器、偏移和重叠边界测试 |
| Day10 | Embedding 请求与响应协议 | U07 前半 | 分批、错序恢复、维度检查的走读 |
| Day11 | Embedding 异常与协议测试 | U07 后半 | 超时、HTTP 错误、坏向量的失败矩阵 |
| Day12 | IndexingService 与向量写入 | U08 前半 | 文本到 IndexedChunk 的数据流图 |
| Day13 | 索引事务与失败恢复 | U08 后半 | 实际 INSERT 后失败的回滚与 FAILED 证据 |
| Day14 | 第二阶段整合复盘 | U04–U08 | 完整上传链、重复请求和进程中断边界解释 |
| Day15 | cosine、过滤与 HNSW | U09 前半 | 手算分数、过滤查询、近似索引说明 |
| Day16 | 检索结果与引用来源 | U09 后半 | 空结果、TOP_K、来源和元数据对照 |
| Day17 | 错误响应与检索日志 | U10 | HTTP/业务码矩阵、计时和日志边界 |
| Day18 | 测试分层与 schema 隔离 | U11 | 替身与真实依赖图、版本表隔离解释 |
| Day19 | 部署与目标环境复验 | U12 前半 | 目标数据库、迁移、启动和模型调用记录 |
| Day20 | 全链复盘与项目讲述 | U12 后半 | 两分钟讲解、演示证据、诚实的未完成清单 |

Day01–05 不要求数据库或付费模型。Day06 开始逐步需要真实 PostgreSQL 与 pgvector；Day07、Day08、Day13 的数据库行为须实测，缺环境时保留相应运行验收为待执行。Day19 才把 PG16 目标容器和真实模型组合做部署验收；如果条件已具备，可以提前准备环境，但不把未来的学习内容提前记为已掌握。

### 3.3 每日学习节奏

一般分为前置复盘 10–15 分钟、问题与机制 25–35 分钟、源码和测试 45–60 分钟、独立练习 30–45 分钟、错因记录与口述 15–20 分钟。根据内容调整，总投入按 2–3 小时估计，完整读懂比按时翻完更重要。

一天结束时分开记录教材交付、工程检查和用户学习。用户尚未完成闭卷解释与练习时，状态写“教材已交付，用户学习进行中或未记录”，不自动跳到下一天。

## 4 单元安排

### U01 项目定位与工程入口

从“为什么接口只返回 chunk 而没有答案”开始，明确调用方与 RAG 中台的分工。说明当前项目为什么属于检索能力服务，哪些条件具备后才可以称为完整问答产品或 Agent。随后认清项目根目录、配置、锁文件、迁移、测试和部署文件的关系。

**阅读资产**：[项目说明](../../README.md)、[pyproject.toml](../../pyproject.toml)、[uv.lock](../../uv.lock)、[启动入口](../../app/__main__.py)、[应用工厂](../../app/main.py)、[API 路由](../../app/api/v1/router.py)。测试入口是 [test_api_contract.py](../../tests/test_api_contract.py) 的 `test_exactly_three_business_operations`。

**练习与产物**：画出“业务方 → 检索服务 → 模型与数据库”的边界图，列出三个业务接口及各自输入输出。核对 Python 版本，运行不依赖外部服务的路由契约测试；如仅能读代码，记录测试尚未运行。

**完成标准**：能解释业务接口与 OpenAPI 文档路由的区别，能指出项目当前没有生成模型、聊天 UI、任务队列和 Agent 循环。不能把自己能打开 README 记成环境已验收。

**面试解释题**：为什么先做三个接口；中台调用方得到结果后还要做什么；为什么不需要先引入 LangChain。

### U02 Python 数据表示与 Pydantic 契约

从“kb_xxx 看起来像 ID，为什么请求仍被拒绝”开始，学习 UUID、类型标注、枚举、dataclass、Pydantic 模型之间的职责。比较外部请求对象、内部 IndexedChunk/SearchHit 和持久化 ORM 对象，说明它们为何不合成一个大对象。

**阅读资产**：[公共 Schema](../../app/schemas/common.py)、[Document Schema](../../app/schemas/document.py)、[RAG Schema](../../app/schemas/rag.py)、[向量接口数据类](../../app/providers/vectorstores/base.py)、[UUID 工具](../../app/utils/id_generator.py)。测试使用 test_api_contract.py 的参数校验与 UUID/时间序列化用例。

**练习与产物**：用合法和非法字典分别构造请求模型，观察未知字段、空白字符串、NUL、非法 UUID 的错误。区分 tenant_id 的外部字符串与 kb_id 的内部 UUID；记录 input 到 JSON output 的类型变化。

**完成标准**：能说明 extra=forbid、字段校验、去空白和保留原始 query 的差别；能解释为什么当前请求携带 top_k 会被拒绝。NUL 检查只处理顶层字符串字段，不把它描述为任意嵌套数据的通用扫描器。

**面试解释题**：Pydantic 验证和数据库约束为什么都要有；IntEnum 为什么在 JSON 中返回整数。

### U03 FastAPI 依赖装配与资源生命周期

从“路由没有创建模型客户端，会话和 Provider 从哪里来”开始，沿 Depends 找到装配入口。理解 Annotated、请求作用域的 Session、应用作用域的 AsyncClient、lifespan 及资源释放，区分异步 I/O 与后台任务。

**阅读资产**：[依赖装配](../../app/api/dependencies.py)、[main.py](../../app/main.py)、[__main__.py](../../app/__main__.py)、[数据库会话](../../app/db/session.py)、[配置](../../app/core/config.py)。测试包括 test_integration.py 的 `test_real_lifespan_and_openai_provider_through_all_three_routes` 及 test_config.py。

**练习与产物**：绘制一次请求的对象创建和释放图，标出哪些对象共享、哪些对象每个请求创建。解释 Windows 的 Selector 入口；列出进程启动前迁移与启动时维度检查的差异。

**完成标准**：能在不看教材的情况下找到 get_session 和 get_embedding 的调用来源；能解释一次成功请求结束时 finally 中 rollback 为什么不撤销此前已提交的事务。能指出配置缓存的影响和 `.env` 相对路径。

**面试解释题**：为什么共享 HTTP 客户端；为什么不能每个请求共享同一个 AsyncSession；async def 是否意味着上传立即返回。

### U04 SQLAlchemy 数据模型与 Alembic 迁移

从“只判断 kb_id，为什么还可能写错租户”开始，解释四张表及复合外键。理解 ORM、SQL 表、约束、普通索引和 HNSW 索引的不同作用，再把模型映射到初始迁移。

**阅读资产**：[ORM Base](../../app/db/base.py)、[KnowledgeBase](../../app/models/knowledge_base.py)、[Document](../../app/models/document.py)、[Chunk](../../app/models/chunk.py)、[RetrievalLog](../../app/models/retrieval_log.py)、[初始迁移](../../migrations/versions/0001_initial.py)、[迁移环境](../../migrations/env.py)。测试入口是 test_integration.py 的 database fixture 和持久化用例。

**练习与产物**：画 ER 图，写明每条复合外键约束哪些字段。生成一次离线迁移 SQL 并逐段解释；有专用测试库时运行 upgrade 和 check。回退练习仅针对已确认可清空的练习库，不能在业务库演示删表。

**完成标准**：能说明 metadata 与 chunk_metadata 的区别；能指出 model 中 Python default 与数据库 server_default 的差异；能解释更改向量维度为什么涉及迁移和重建索引。

**面试解释题**：查询过滤和复合外键分别防什么错误；已有数据库改模型后为什么不能依赖 create_all。

### U05 创建知识库与基础事务

从“flush 已经插入了数据，为什么还需要 commit”开始，按一个最短请求完整穿过路由、Service、Repository 和 PostgreSQL。利用简单路径先建立事务心智模型，再进入复杂索引流程。

**阅读资产**：[知识库路由](../../app/api/v1/routes/knowledge_bases.py)、[KnowledgeBaseService](../../app/services/knowledge_base_service.py)、[KnowledgeBaseRepository](../../app/repositories/knowledge_base_repository.py)、[KnowledgeBase Schema](../../app/schemas/knowledge_base.py)。测试使用 test_create_upload_retrieve_and_persist_log 和 test_success_envelope_serializes_uuid_and_timestamp。

**练习与产物**：按输入、数据库动作、事务边界和输出画四步图。有测试库时分别观察 flush 后 rollback、commit 后新会话读取的结果；没有数据库时保留为待实测练习，不能编写伪输出。

**完成标准**：能说明 ID 与 created_at 从哪里产生，解释 Repository 不自行 commit 的原因；知道知识库重名当前没有去重或唯一名称约束。

**面试解释题**：为什么事务由 Service 决定；如果把 commit 放到每个 Repository 方法内会限制什么后续组合。

### U06 文本规范化与字符切片

从“中文字符偏移与模型 token 是不是一回事”开始，手算窗口，再走读解析器与切片器。说明换行规范化、BOM、纯空白片段、重叠和边界的作用，并将位置用于引用解释。

**阅读资产**：[DocumentParser 抽象](../../app/providers/parsers/base.py)、[PlainTextParser](../../app/providers/parsers/plain_text.py)、[TextSplitter](../../app/utils/text_splitter.py)、[IndexingService](../../app/services/indexing_service.py)。测试使用 test_text_processing.py 的四类测试函数及参数化用例。

**练习与产物**：闭卷实现一个大小为 8、重叠为 2 的 Unicode 切片器，并为刚好一个窗口、最后不足一窗、纯空白、中文与换行写测试。不要改生产切片器来使实验更容易通过。

**完成标准**：能用规范化文本的切片表达式还原每个 TextChunk.content，解释为何需要 overlap<size；能指出当前没有段落切片、token 预算、PDF 页码和 Markdown 结构解析。

**面试解释题**：chunk size 和 overlap 的取舍是什么；为什么引用位置不能直接当成原文件字节位置。

### U07 Embedding 协议与异常校验

从“模型响应成功但向量次序错了会发生什么”开始，先理解输入文本与输出向量的一一对应，再学习分批、索引排序、维度、非有限数和零向量检查。

**阅读资产**：[EmbeddingProvider](../../app/providers/embedding/base.py)、[OpenAI-compatible 实现](../../app/providers/embedding/openai_compatible.py)、[Settings](../../app/core/config.py)、[EmbeddingError](../../app/core/exceptions.py)。测试入口是 test_embedding_provider.py。

**练习与产物**：在独立测试中用 MockTransport 返回乱序 index、缺少结果、错误维度、零向量、NaN、401/429/500 和超时，记录每类错误如何映射。说明批次是串行执行，当前没有重试。

**完成标准**：能手写本项目实际发送的 JSON 字段，解释为什么配置 768 维不会自动让默认模型返回 768 维；能说明默认模型名、模型协议与真实账号已验收之间的区别。

**面试解释题**：同维度模型能否直接互换；哪些异常应该返回给业务方，哪些上游信息不应原样输出。

### U08 文档同步索引与失败恢复

从“上传返回失败后，数据库为什么还应该保留文档”开始，将前面各层组合起来。这个单元重点是实际事务时间线，不应只把各个类的功能摘要拼在一起。

**阅读资产**：[文档路由](../../app/api/v1/routes/documents.py)、[DocumentService](../../app/services/document_service.py)、[DocumentRepository](../../app/repositories/document_repository.py)、[IndexingService](../../app/services/indexing_service.py)、[PgVectorStore](../../app/providers/vectorstores/pgvector.py)、[ChunkRepository](../../app/repositories/chunk_repository.py)。测试使用两个失败恢复用例和 test_multichunk_indexing_and_top_k_limit。

**练习与产物**：绘制 PROCESSING 提交、外部模型调用、chunk flush、SUCCESS 提交、失败 rollback、FAILED 提交的时间线。在专用测试库通过当前失败用例观察数据库前后状态；对照模型故障与真实 SQL 事务失败两种路径。

**完成标准**：能指出两个主要提交阶段及失败分支独立事务；能解释进程强制终止、重复上传、数据库不可用仍存在什么边界。知道当前没有原文件存储、自动重试、幂等与后台状态查询接口。

**面试解释题**：为什么不能失败后 rollback 一次就返回；把流程迁入 Celery 还需要补哪些一致性能力。

### U09 pgvector 召回与引用元数据

从“相似度最高的片段属于另一个知识库怎么办”开始，把向量距离、过滤和排序结合起来。区分最大召回数量、索引近似性、空结果和业务相关性。

**阅读资产**：[RagService](../../app/services/rag_service.py)、[VectorStore 抽象](../../app/providers/vectorstores/base.py)、[PgVectorStore](../../app/providers/vectorstores/pgvector.py)、[ChunkRepository](../../app/repositories/chunk_repository.py)、[RAG Schema](../../app/schemas/rag.py)。测试使用 test_tenant_and_knowledge_base_isolation、test_empty_knowledge_base_returns_empty_structured_result、test_create_upload_retrieve_and_persist_log。

**练习与产物**：用二维非零向量手算同向和正交的 cosine 分数，再指出真实代码中的距离排序和 score 转换。列出查询的 tenant_id、kb_id、SUCCESS 三个条件，分析删除任一条件会产生的具体错误。

**完成标准**：能解释 score=1-distance 和 [-1,1] 的意义；知道 HNSW 索引存在不等于所有查询一定使用它；能说明引用 metadata 的生成位置，且不会把已实现过滤称为完整鉴权。

**面试解释题**：为什么相似度不是概率；top_k=5 为什么可能只返回 2 条；哪些问题可能更适合词项检索，但当前是否已经实现。

### U10 错误协议与检索日志

从“同样是模型超时，上传与检索为什么返回不同业务码”开始，理解异常转换的层次。把 request validation、业务错误、框架错误与非预期错误分别对应到当前处理器，再走读成功检索日志。

**阅读资产**：[异常处理器](../../app/core/exceptions.py)、[日志配置](../../app/core/logging.py)、[RagService](../../app/services/rag_service.py)、[RetrievalLogRepository](../../app/repositories/retrieval_log_repository.py)、[RetrievalLog](../../app/models/retrieval_log.py)。测试使用 test_api_contract.py 的错误用例与 test_create_upload_retrieve_and_persist_log 的日志断言。

**练习与产物**：建立失败输入、抛出层、HTTP 状态、业务码、data 和数据库影响的矩阵。找到 latency_ms 的实际计时位置，列出未被该数值覆盖的步骤。

**完成标准**：能解释 50201 与 50202、50000 与 50002 的区别；明确失败检索没有被当前成功日志表完整记录，日志保存失败也没有设计为可忽略。

**面试解释题**：为什么不回传完整内部异常；有日志与有完整可观测体系之间还缺哪些环节。

### U11 测试分层与数据库隔离

从“31 项通过和 38 项通过能否表达同一个结论”开始，区分参数化用例数量、测试函数数量、跳过数量以及真实依赖和替身。说明为什么契约测试不启动 lifespan，数据库集成又必须真跑迁移。

**阅读资产**：[tests/conftest.py](../../tests/conftest.py)、[test_api_contract.py](../../tests/test_api_contract.py)、[test_embedding_provider.py](../../tests/test_embedding_provider.py)、[test_integration.py](../../tests/test_integration.py)、[migrations/env.py](../../migrations/env.py)。

**练习与产物**：画出每类测试替换了什么、保留了什么。解释随机 schema、search_path、版本表 schema 和 `_test` 库名检查的不同目的；在有 public.alembic_version 的专用测试库验证新 schema 仍得到四张业务表。

**完成标准**：能解读 passed/deselected/skipped；能说明固定测试向量证明了排序和过滤行为，但没有证明真实语义召回效果。不会把旧日期的通过记录复制成今天的新结果。

**面试解释题**：为什么一个 Mock 不能证明整个系统；实际 INSERT 后触发 SQL 错误的测试多证明了什么。

### U12 部署复验与项目讲述

从“代码测试都绿了，为什么还不能说目标容器已验收”开始，完成配置、迁移、启动、三个接口和数据结果的串联。将工程结论整理成能复现的证据，再形成简洁的项目讲解。

**阅读资产**：[Dockerfile](../../Dockerfile)、[docker-compose.yml](../../docker-compose.yml)、[.env.example](../../.env.example)、[项目 README](../../README.md)、[历史验证记录](../../VERIFICATION.md)、本手册第 13 节。

**练习与产物**：在可用环境中完成目标 PG16 与 pgvector 0.8.1 的启动，运行迁移和三个接口，保存请求 ID、状态、片段和日志。真实模型凭据未提供时保留该验收项为待执行，不在正式 Provider 中注入测试向量。

**完成标准**：能分别描述客户端配置、Engine 状态、容器健康、表结构、真实模型调用和接口结果；能用两分钟说明项目定位、主链路、一个事务取舍、一个失败边界和真实证据。

**面试解释题**：当前项目最有依据的工程点是什么；如果要提升检索效果，第一套对照实验应记录哪些指标，哪些指标目前没有数据。

## 5 当前进度

此表是学习进度的唯一维护位置。代码已经实现不代表完整教材已交付，也不代表用户已掌握。用户尚未提供学习记录，所以不能代填通过。

| 范围 | 当前实现 | 完整教材 | 用户学习 |
| --- | --- | --- | --- |
| 交接手册与学习总纲 | 已依据现有工程建立 | 已建立，已细化为 3 阶段 20 Day | 用户已同意开启学习 |
| 第一阶段 Day01 | 相关源码已存在 | 已交付教材、实验、学习模板和验收记录 | 待用户独立完成 |
| 第一阶段 Day02–05 | 相关源码已存在 | 待编写 | 未记录 |
| 第二阶段 Day06–14 | 相关源码已存在 | 待编写 | 未记录 |
| 第三阶段 Day15–20 | 相关源码已存在 | 待编写 | 未记录 |
| 目标 PG16 容器与真实模型闭环 | 配置和 Provider 已存在 | 启动步骤已给出 | 完整目标组合待实际验收 |
| 混合检索、rerank、异步任务、ACL、评测 | 未实现 | 不属于基线单元 | 未安排 |

当前学习任务是完成第一阶段 Day01 的项目地图、契约实验和闭卷解释。下一份教材为 Day02 的 Python 数据表示；Day01 用户学习尚未确认完成，不在进度表中替用户推进。

## 6 后续教材的统一写法

### 6.1 每份教材要形成一条解释链

每份教材先承接已学能力，给出一个项目内可观察的问题，再引入解决问题所需的概念，连接到真实代码与测试。随后给出运行步骤、失败复现、练习与讲述要求，不用术语堆砌代替因果说明。

建议结构如下：

1. 从上一单元的哪段能力继续，这次要回答什么问题。
2. 必要前置知识及本单元范围。
3. 生产源码和测试资产清单，注明方法与测试名。
4. 原理推导，必要时配流程图、时序图或 ER 图。
5. 关键方法走读，说明输入、依赖、动作、输出、异常和事务归属。
6. 测试矩阵，说明受控输入、断言、是否真实依赖、能证明和不能证明什么。
7. 可执行命令、前置条件、期望行为及实际运行结果。
8. 失败复现与排查，不改坏正式项目。
9. 闭卷复刻或等价改动、针对本单元的 Python/SQL/异步练习。
10. 面试解释题、学习验收及下一单元需要带走的知识。

不强制统一行数，也不按页面长度判断质量。核心实现和断言应足够完整，使学习者不依赖聊天历史也能找到并解释；但不要在每一章复制整个仓库。

### 6.2 源码引用标准

教材中的文件路径必须实际存在，方法和测试名必须核对当前代码。讲一个方法时应说明调用者、参数来源、执行顺序、状态变化及失败后的结果。只写“这里使用依赖注入实现解耦”不能替代具体依赖的装配过程。

短而关键的方法可以完整呈现，长文件优先按连贯逻辑段引用，并保留到原文件的链接。若使用教学简化代码，应明确标为独立实验，说明与生产实现的差别，不把简化实验冒充项目实际行为。

### 6.3 测试和失败演练标准

每个有实质机制的单元至少解释一个正常场景和一个边界或失败场景。复杂整合单元 U08、U09、U11、U12 应分别覆盖外部调用、数据库或状态、输入或配置三个维度的故障；某一维度与本单元无关时说明原因，不硬凑题目。

失败实验要写清楚前置数据、操作、预期状态和恢复方式。实际运行过才给出实际输出；没有运行时提供期望行为并标为待复验。对于有费用或需要凭据的实验，先用受控替身理解机制，真实链路另外验收。

### 6.4 图表标准

图表用于澄清对象关系、调用顺序和事务边界，图中每个节点都应能对应源码或外部依赖。默认使用 Markdown Mermaid，文本和链接保持可读；不为装饰而引入前端项目或额外服务。

表格适合字段、版本、测试矩阵、错误码和状态对照。长期解释应使用连贯段落，避免把整章正文塞进表格。

## 7 三种验收分别记录

| 验收类型 | 应检查什么 | 谁能记录 |
| --- | --- | --- |
| 工程行为 | 相关测试、命令、环境与真实结果，是否有 skipped 或替身 | 执行者记录可复核证据 |
| 教材质量 | 源码引用、解释链、测试断言、失败演练、练习和边界是否完整 | 编写者或审查者逐项重读核对 |
| 用户学习 | 能否闭卷解释、复刻、分析错误并回答追问 | 由用户自己完成与反馈 |

纯文档任务不必为了“看看状态”重复构建和启动整个系统；检查应与改动和结论相关。本次文档完成也不意味着所有学习单元完成。若出现引用不一致，先核对源码、Schema、依赖锁和运行证据，再修正文档；不通过修改业务实现来迎合错误教材。

## 8 学习记录模板

每完成一个单元，可以在本文件下方追加简短记录，或由用户选择独立笔记。不要用 AI 代写的标准答案替代用户实际表现。

```text
单元与日期：
练习目录：
我能独立解释的问题：
闭卷复刻的文件或行为：
实际运行命令与结果：
本次遇到的真实错误及根因：
一个尚不能解释的问题：
下一次复习日期：
用户学习状态：未开始 / 进行中 / 已完成本单元要求
```

推荐每个单元完成四件事：脱离教材解释一次主问题；独立实现一个小机制或等价改动；记录一个真实错误；回答一道与当前代码直接有关的追问。对 SQL、算法和 Python 基础的练习按主题安排，不照搬 Java/JVM 题单。

## 9 教材任务卡模板

```text
本次任务：编写用户选定 Day 的完整学习教材，并核对它对应的 U 单元范围。
项目根目录：C:\path\to\rag-center
交接入口：docs\交接文档及学习路线\RAG中台_交接与学习启动手册.md
范围来源：本总纲第 3.2 节对应 Day 行及第 4 节对应 U 单元。
产物位置：docs\学习单元\对应阶段\RAG中台_DayNN_主题.md

先核对对应源码、测试和现有文档；如果已存在该单元的未完成稿，在同一份文档上继续。
采用问题、机制、真实源码、测试、失败复现、独立练习和面试解释的完整结构。
本次默认只改文档，不新增业务接口和基础设施；需要修复真实代码问题时先说明发现及影响。
运行结果附日期与环境，历史验证只引用原日期；未执行项明确记录。
提交前重读教材与引用文件，核对路径、方法、测试名、请求字段、错误码和数据库影响。
本次教材交付与用户学习完成分别报告，不自动推进下一单元。
```

## 10 基线之后的扩展候选

完成基线学习后，可由用户选择真实场景，再确定扩展路线。优先要能用问题集、相关片段标注和对照实验解释现有检索的缺陷；之后再讨论混合检索、重排、异步索引、权限或其他向量库。

这些候选能力不在本次固定为新的技术栈，也不预设必须拆成多少天。候选方向应各自写出要解决的问题、最小改动、测试方法、数据与指标、故障边界及回退方式，再进入实现。
