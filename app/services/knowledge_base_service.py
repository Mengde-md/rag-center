from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import KnowledgeBaseNotFound
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseCreated


class KnowledgeBaseService:
    def __init__(self, session: AsyncSession, repository: KnowledgeBaseRepository):
        self.session = session
        self.repository = repository

    async def create(self, request: KnowledgeBaseCreate) -> KnowledgeBaseCreated:
        kb = await self.repository.create(request.tenant_id, request.name, request.description)
        await self.session.commit()
        return KnowledgeBaseCreated(
            kb_id=kb.id, tenant_id=kb.tenant_id, name=kb.name, created_at=kb.created_at
        )

    async def require(self, tenant_id: str, kb_id: UUID) -> None:
        if await self.repository.get(tenant_id, kb_id) is None:
            raise KnowledgeBaseNotFound()
