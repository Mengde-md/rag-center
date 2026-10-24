from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ExternalId, RequestModel, Title


class KnowledgeBaseCreate(RequestModel):
    tenant_id: ExternalId
    name: Title
    description: str | None = Field(default=None, max_length=5000)


class KnowledgeBaseCreated(BaseModel):
    kb_id: UUID
    name: str
    tenant_id: str
    created_at: datetime
