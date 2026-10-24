from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.document import DocumentStatus
from app.schemas.common import ExternalId, RequestModel, Title


class DocumentUpload(RequestModel):
    tenant_id: ExternalId
    kb_id: UUID
    title: Title
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content must not be blank")
        if "\x00" in value:
            raise ValueError("content must not contain NUL characters")
        return value


class DocumentUploaded(BaseModel):
    document_id: UUID
    kb_id: UUID
    status: DocumentStatus
    chunk_count: int
