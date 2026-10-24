from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase


class KnowledgeBaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tenant_id: str, name: str, description: str | None) -> KnowledgeBase:
        kb = KnowledgeBase(tenant_id=tenant_id, name=name, description=description)
        self.session.add(kb)
        await self.session.flush()
        return kb

    async def get(self, tenant_id: str, kb_id: UUID) -> KnowledgeBase | None:
        return await self.session.scalar(
            select(KnowledgeBase).where(
                KnowledgeBase.tenant_id == tenant_id, KnowledgeBase.id == kb_id
            )
        )
