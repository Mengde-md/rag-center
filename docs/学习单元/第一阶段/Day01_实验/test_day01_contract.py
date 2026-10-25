"""Day01 teaching tests; run explicitly because production testpaths is tests/."""

import importlib.util
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_embedding, get_knowledge_base_service, get_session
from app.main import create_app
from app.schemas.knowledge_base import KnowledgeBaseCreated

MODULE_PATH = Path(__file__).with_name("route_probe.py")
SPEC = importlib.util.spec_from_file_location("day01_route_probe", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


@pytest.fixture
def schema():
    return create_app().openapi()


@pytest.fixture
def client(monkeypatch):
    async def forbidden_database_startup(*args, **kwargs):
        raise AssertionError("Day01 must not run the database lifespan")

    monkeypatch.setattr("app.main.verify_database", forbidden_database_startup)
    application = create_app()

    async def no_database():
        yield None

    application.dependency_overrides[get_session] = no_database
    application.dependency_overrides[get_embedding] = lambda: None
    # Intentionally no 'with': HTTP contracts can be tested without application startup.
    client = TestClient(application, raise_server_exceptions=True)
    yield client
    client.close()


def test_real_app_exposes_three_post_operations(schema):
    assert len(probe.assert_core_contract(schema)) == 3


def test_path_metadata_is_not_a_business_operation(schema):
    altered = deepcopy(schema)
    altered["paths"]["/api/v1/rag/retrieve"]["parameters"] = []
    assert len(probe.assert_core_contract(altered)) == 3


def test_missing_operation_is_reported(schema):
    altered = deepcopy(schema)
    del altered["paths"]["/api/v1/rag/retrieve"]
    with pytest.raises(ValueError, match="missing: POST /api/v1/rag/retrieve"):
        probe.assert_core_contract(altered)


def test_wrong_method_reports_missing_and_unexpected_operations(schema):
    altered = deepcopy(schema)
    item = altered["paths"]["/api/v1/rag/retrieve"]
    item["get"] = item.pop("post")
    with pytest.raises(ValueError) as error:
        probe.assert_core_contract(altered)
    assert "missing: POST /api/v1/rag/retrieve" in str(error.value)
    assert "unexpected: GET /api/v1/rag/retrieve" in str(error.value)


def test_extra_operation_is_reported(schema):
    altered = deepcopy(schema)
    altered["paths"]["/api/v1/answer"] = {"post": {}}
    with pytest.raises(ValueError, match="unexpected: POST /api/v1/answer"):
        probe.assert_core_contract(altered)


@pytest.mark.parametrize(
    "path,status,code,message",
    [
        ("/api/v1/missing", 404, 40400, "Not Found"),
        ("/api/v1/documents/upload", 405, 40500, "Method Not Allowed"),
    ],
)
def test_framework_errors_use_the_project_envelope(client, path, status, code, message):
    response = client.get(path)
    assert response.status_code == status
    assert response.json() == {"code": code, "msg": message, "data": None}


def test_mock_create_checks_http_contract_without_database_writes(client):
    calls = []

    class LearningService:
        async def create(self, body):
            calls.append((body.name, body.tenant_id))
            return KnowledgeBaseCreated(
                kb_id=UUID("00000000-0000-4000-8000-000000000001"),
                name=body.name,
                tenant_id=body.tenant_id,
                created_at=datetime(2026, 10, 25, tzinfo=UTC),
            )

    client.app.dependency_overrides[get_knowledge_base_service] = LearningService
    response = client.post(
        "/api/v1/knowledge-bases/create", json={"name": "学习知识库", "tenant_id": "tenant_demo"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["code"] == 0 and result["msg"] == "success"
    assert result["data"]["kb_id"] == "00000000-0000-4000-8000-000000000001"
    assert result["data"]["created_at"] == "2026-10-25T00:00:00Z"
    assert calls == [("学习知识库", "tenant_demo")]


@pytest.mark.parametrize(
    "body",
    [
        {"name": " ", "tenant_id": "tenant_demo"},
        {"name": "学习知识库", "tenant_id": "tenant_demo", "unexpected": True},
    ],
)
def test_bad_input_does_not_reach_the_learning_service(client, body):
    class ForbiddenService:
        async def create(self, body):
            raise AssertionError("invalid requests must not call the service")

    client.app.dependency_overrides[get_knowledge_base_service] = ForbiddenService
    response = client.post("/api/v1/knowledge-bases/create", json=body)
    assert response.status_code == 422
    assert response.json()["code"] == 42201
    assert all("input" not in item for item in response.json()["data"])
