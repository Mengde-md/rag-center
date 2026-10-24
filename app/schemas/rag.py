from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ExternalId, RequestModel


class RetrievalRequest(RequestModel):
    tenant_id: ExternalId
    kb_id: UUID
    user_id: ExternalId
    query: str = Field(min_length=1, max_length=8000)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        if not value.strip() or "\x00" in value:
            raise ValueError("query must be non-blank and contain no NUL characters")
        return value


class RetrievedChunk(BaseModel):
    document_id: UUID
    chunk_id: UUID
    title: str
    content: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalMetadata(BaseModel):
    retrieval_log_id: UUID
    top_k: int
    vector_store: str


class RetrievalResult(BaseModel):
    query: str
    kb_id: UUID
    retrieved_chunks: list[RetrievedChunk]
    metadata: RetrievalMetadata
