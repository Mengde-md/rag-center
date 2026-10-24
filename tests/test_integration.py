"""Real pgvector tests. Use a dedicated database whose name ends with _test.

Only EmbeddingProvider is replaced by a deterministic fixture: PostgreSQL tables,
migrations, transactions, foreign keys, vector writes/searches, and logs are real.
"""

import os
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.schema import CreateSchema, DropSchema

from app.api.dependencies import get_embedding, get_session, get_vector_store
from app.core.config import Settings
from app.core.exceptions import EmbeddingError
from app.main import create_app
from app.models import Chunk, Document, DocumentStatus, RetrievalLog
from app.providers.embedding.base import EmbeddingProvider
from app.providers.vectorstores.pgvector import PgVectorStore
from app.repositories.chunk_repository import ChunkRepository
from app.utils.id_generator import generate_id

pytestmark = pytest.mark.integration
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DeterministicEmbedding(EmbeddingProvider):
    def __init__(self, dimensions):
        self.dimensions = dimensions

    async def embed_texts(self, texts):
        return [
            ([1.0, 0.0] if "refund" in value else [0.0, 1.0]) + [0.0] * (self.dimensions - 2)
            for value in texts
        ]


@pytest_asyncio.fixture
async def database():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("set TEST_DATABASE_URL to run real PostgreSQL + pgvector tests")
    if not (make_url(url).database or "").endswith("_test"):
        pytest.fail("TEST_DATABASE_URL must point to a dedicated database ending in _test")
    schema = "rag_test_" + generate_id().hex
    admin_engine = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public"))
        connection.execute(CreateSchema(schema))
    options = {"options": f"-csearch_path={schema},public"}
    migration_engine = create_engine(url, connect_args=options)
    async_engine = create_async_engine(url, connect_args=options)
    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    try:
        config = Config(str(PROJECT_ROOT / "alembic.ini"))
        with migration_engine.begin() as connection:
            config.attributes["connection"] = connection
            # Do not inherit public.alembic_version through the search path when it exists.
            config.attributes["version_table_schema"] = schema
            command.upgrade(config, "head")
            tables = set(
                connection.scalars(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = :schema"
                    ),
                    {"schema": schema},
                )
            )
            assert tables == {
                "alembic_version",
                "knowledge_bases",
                "documents",
                "chunks",
                "retrieval_logs",
            }
        yield factory
    finally:
        await async_engine.dispose()
        migration_engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(DropSchema(schema, cascade=True))
        admin_engine.dispose()


@pytest_asyncio.fixture
async def api(database):
    settings = Settings(_env_file=None)
    app = create_app(settings)

    async def session_override():
        async with database() as session:
            try:
                yield session
            finally:
                await session.rollback()

    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[get_embedding] = lambda: DeterministicEmbedding(
        settings.embedding_dimensions
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        yield client, app


async def create_kb(client, tenant="tenant-a"):
    response = await client.post(
        "/api/v1/knowledge-bases/create", json={"tenant_id": tenant, "name": "政策"}
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["kb_id"]


def document_body(kb_id, content="refund available within seven days", tenant="tenant-a"):
    return {"tenant_id": tenant, "kb_id": kb_id, "title": "policy", "content": content}


def retrieval_body(kb_id, tenant="tenant-a"):
    return {"tenant_id": tenant, "kb_id": kb_id, "user_id": "business-user", "query": "refund?"}


async def test_create_upload_retrieve_and_persist_log(api, database):
    client, _ = api
    kb_id = await create_kb(client)
    upload = await client.post("/api/v1/documents/upload", json=document_body(kb_id))
    assert upload.status_code == 200, upload.text
    assert upload.json()["data"]["status"] == 1
    assert upload.json()["data"]["chunk_count"] == 1
    # A second, less relevant document proves real vector ranking, not insertion order.
    await client.post("/api/v1/documents/upload", json=document_body(kb_id, "shipping policy"))
    response = await client.post("/api/v1/rag/retrieve", json=retrieval_body(kb_id))
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert "context_text" not in result
    assert len(result["retrieved_chunks"]) == 2
    assert result["retrieved_chunks"][0]["score"] == pytest.approx(1)
    assert result["retrieved_chunks"][1]["score"] == pytest.approx(0)
    assert "refund" in result["retrieved_chunks"][0]["content"]
    assert result["retrieved_chunks"][0]["metadata"]["start_char"] == 0
    async with database() as session:
        log = await session.scalar(select(RetrievalLog))
        assert str(log.id) == result["metadata"]["retrieval_log_id"]
        assert log.user_id == "business-user"
        assert log.retrieved_chunks == result["retrieved_chunks"]
        assert log.latency_ms >= 0


async def test_tenant_and_knowledge_base_isolation(api):
    client, _ = api
    own_kb = await create_kb(client)
    other_kb = await create_kb(client)
    foreign_kb = await create_kb(client, "tenant-b")
    await client.post("/api/v1/documents/upload", json=document_body(own_kb, "refund own"))
    await client.post("/api/v1/documents/upload", json=document_body(other_kb, "refund other kb"))
    await client.post(
        "/api/v1/documents/upload", json=document_body(foreign_kb, "refund foreign", "tenant-b")
    )
    result = (await client.post("/api/v1/rag/retrieve", json=retrieval_body(own_kb))).json()
    assert [chunk["content"] for chunk in result["data"]["retrieved_chunks"]] == ["refund own"]
    for path, body in [
        ("/api/v1/documents/upload", document_body(own_kb, tenant="tenant-b")),
        ("/api/v1/rag/retrieve", retrieval_body(own_kb, "tenant-b")),
    ]:
        response = await client.post(path, json=body)
        assert response.status_code == 404
        assert response.json()["code"] == 40001


async def test_empty_knowledge_base_returns_empty_structured_result(api):
    client, _ = api
    kb_id = await create_kb(client)
    result = (await client.post("/api/v1/rag/retrieve", json=retrieval_body(kb_id))).json()
    assert result["code"] == 0
    assert result["data"]["retrieved_chunks"] == []


async def test_embedding_failure_preserves_failed_document(api, database):
    client, app = api
    kb_id = await create_kb(client)

    class BrokenEmbedding(EmbeddingProvider):
        async def embed_texts(self, texts):
            raise EmbeddingError("embedding provider timed out")

    app.dependency_overrides[get_embedding] = BrokenEmbedding
    response = await client.post("/api/v1/documents/upload", json=document_body(kb_id))
    assert response.status_code == 502
    assert response.json()["data"]["status"] == 2
    async with database() as session:
        document = await session.scalar(select(Document))
        assert document.status == DocumentStatus.FAILED
        assert document.error_message == "embedding provider timed out"
        assert await session.scalar(select(func.count()).select_from(Chunk)) == 0


async def test_vector_write_failure_rolls_back_chunks_and_marks_document_failed(api, database):
    client, app = api
    kb_id = await create_kb(client)

    class FailAfterWrite(PgVectorStore):
        async def add_chunks(self, chunks):
            await super().add_chunks(chunks)
            # Abort the real transaction after INSERT to test recovery from failed SQL.
            await self.chunks.session.execute(text("SELECT 1 / 0"))

    from typing import Annotated

    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession

    def failing_store(session: Annotated[AsyncSession, Depends(get_session)]):
        return FailAfterWrite(ChunkRepository(session))

    app.dependency_overrides[get_vector_store] = failing_store
    response = await client.post("/api/v1/documents/upload", json=document_body(kb_id))
    assert response.status_code == 500
    assert response.json()["data"]["status"] == 2
    async with database() as session:
        assert await session.scalar(select(func.count()).select_from(Chunk)) == 0
        document = await session.scalar(select(Document))
        assert document.status == 2
        assert document.chunk_count == 0


async def test_multichunk_indexing_and_top_k_limit(api, database):
    client, _ = api
    kb_id = await create_kb(client)
    content = "refund within seven days. " * 200
    response = await client.post("/api/v1/documents/upload", json=document_body(kb_id, content))
    assert response.status_code == 200
    count = response.json()["data"]["chunk_count"]
    assert count > 5
    async with database() as session:
        chunks = list(await session.scalars(select(Chunk)))
        assert len(chunks) == count
        assert len({chunk.id for chunk in chunks}) == count
        assert all(
            chunk.content
            == content[chunk.chunk_metadata["start_char"] : chunk.chunk_metadata["end_char"]]
            for chunk in chunks
        )
    result = (await client.post("/api/v1/rag/retrieve", json=retrieval_body(kb_id))).json()
    assert len(result["data"]["retrieved_chunks"]) == result["data"]["metadata"]["top_k"]


async def test_real_lifespan_and_openai_provider_through_all_three_routes(database):
    from app.providers.embedding.openai_compatible import OpenAICompatibleEmbeddingProvider

    async with database() as session:
        search_path = await session.scalar(text("SHOW search_path"))
    url = make_url(os.environ["TEST_DATABASE_URL"]).update_query_dict(
        {"options": f"-csearch_path={search_path.replace(' ', '')}"}
    )
    settings = Settings(
        _env_file=None,
        database_url=url.render_as_string(hide_password=False),
        model_api_key="test-key",
    )

    def embedding_response(request):
        import json

        inputs = json.loads(request.content)["input"]
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": i, "embedding": [1.0] + [0.0] * (settings.embedding_dimensions - 1)}
                    for i in range(len(inputs))
                ]
            },
        )

    app = create_app(settings)
    async with httpx.AsyncClient(transport=httpx.MockTransport(embedding_response)) as model_client:
        provider = OpenAICompatibleEmbeddingProvider(model_client, settings)
        app.dependency_overrides[get_embedding] = lambda: provider
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                assert (await client.get("/openapi.json")).status_code == 200
                kb_id = await create_kb(client)
                upload = await client.post("/api/v1/documents/upload", json=document_body(kb_id))
                assert upload.json()["data"]["status"] == 1
                result = await client.post("/api/v1/rag/retrieve", json=retrieval_body(kb_id))
                assert result.json()["data"]["retrieved_chunks"][0]["score"] == pytest.approx(1)
