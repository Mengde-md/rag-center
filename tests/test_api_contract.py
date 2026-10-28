from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_document_service,
    get_embedding,
    get_knowledge_base_service,
    get_session,
)
from app.core.exceptions import KnowledgeBaseNotFound
from app.main import create_app
from app.schemas.document import DocumentUpload


async def no_database():
    yield None


@pytest.fixture
def client():
    app = create_app()
    app.dependency_overrides[get_session] = no_database
    app.dependency_overrides[get_embedding] = lambda: None
    # No context manager: these contract tests intentionally do not start the DB lifespan.
    return TestClient(app, raise_server_exceptions=False)


def test_exactly_three_business_operations(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {
        "/api/v1/knowledge-bases/create",
        "/api/v1/documents/upload",
        "/api/v1/rag/retrieve",
    }
    assert all(set(path) == {"post"} for path in paths.values())


@pytest.mark.parametrize(
    "path,body",
    [
        ("/api/v1/knowledge-bases/create", {"name": " ", "tenant_id": "tenant"}),
        (
            "/api/v1/documents/upload",
            {"tenant_id": "t", "kb_id": "bad", "title": "t", "content": "c"},
        ),
        ("/api/v1/rag/retrieve", {"query": ""}),
    ],
)
def test_validation_uses_envelope(client, path, body):
    response = client.post(path, json=body)
    assert response.status_code == 422
    assert response.json()["code"] == 42201
    assert set(response.json()) == {"code", "msg", "data"}
    assert all("input" not in error for error in response.json()["data"])


@pytest.mark.parametrize("content", ["\ufeff", "\ufeff \r\n", "\ufeff\ufeff\t"])
def test_bom_only_documents_are_rejected_before_indexing(client, content):
    calls = []

    class ForbiddenService:
        async def upload(self, body):
            calls.append(body)
            raise AssertionError("blank documents must not enter the indexing service")

    client.app.dependency_overrides[get_document_service] = lambda: ForbiddenService()
    response = client.post(
        "/api/v1/documents/upload",
        json={
            "tenant_id": "tenant",
            "kb_id": "00000000-0000-4000-8000-000000000001",
            "title": "空文档",
            "content": content,
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == 42201
    assert any(error["loc"] == ["body", "content"] for error in response.json()["data"])
    assert all("input" not in error for error in response.json()["data"])
    assert calls == []


def test_document_validation_preserves_bom_and_line_endings_for_parser():
    content = "\ufeff# 政策\r\n用户可在七天内申请退款。"
    request = DocumentUpload(
        tenant_id="tenant",
        kb_id=UUID("00000000-0000-4000-8000-000000000001"),
        title="退款政策",
        content=content,
    )
    assert request.content == content


def test_router_errors_use_envelope(client):
    assert client.get("/missing").json() == {"code": 40400, "msg": "Not Found", "data": None}
    response = client.get("/api/v1/documents/upload")
    assert response.status_code == 405
    assert response.json()["code"] == 40500


def test_domain_and_unexpected_errors_use_envelope(client):
    class MissingService:
        async def create(self, body):
            raise KnowledgeBaseNotFound()

    client.app.dependency_overrides[get_knowledge_base_service] = lambda: MissingService()
    body = {"name": "test", "tenant_id": "tenant"}
    assert client.post("/api/v1/knowledge-bases/create", json=body).json() == {
        "code": 40001,
        "msg": "knowledge base not found",
        "data": None,
    }

    class BrokenService:
        async def create(self, body):
            raise RuntimeError("secret-data")

    client.app.dependency_overrides[get_knowledge_base_service] = lambda: BrokenService()
    response = client.post("/api/v1/knowledge-bases/create", json=body)
    assert response.status_code == 500
    assert response.json() == {"code": 50000, "msg": "internal server error", "data": None}


def test_success_envelope_serializes_uuid_and_timestamp(client):
    from datetime import UTC, datetime

    from app.schemas.knowledge_base import KnowledgeBaseCreated

    class CreateService:
        async def create(self, body):
            return KnowledgeBaseCreated(
                kb_id=UUID("00000000-0000-4000-8000-000000000001"),
                name=body.name,
                tenant_id=body.tenant_id,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            )

    client.app.dependency_overrides[get_knowledge_base_service] = lambda: CreateService()
    response = client.post(
        "/api/v1/knowledge-bases/create", json={"name": "政策", "tenant_id": "tenant"}
    )
    assert response.status_code == 200
    assert response.json()["code"] == 0
    assert response.json()["data"]["created_at"] == "2026-01-01T00:00:00Z"
