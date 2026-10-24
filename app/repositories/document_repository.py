from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tenant_id: str, kb_id: UUID, title: str) -> Document:
        document = Document(tenant_id=tenant_id, kb_id=kb_id, title=title)
        self.session.add(document)
        await self.session.flush()
        return document

    async def set_status(
        self,
        document_id: UUID,
        *,
        tenant_id: str,
        status: DocumentStatus,
        chunk_count: int = 0,
        error_message: str | None = None,
    ) -> None:
        await self.session.execute(
            update(Document)
            .where(Document.id == document_id, Document.tenant_id == tenant_id)
            .values(status=status, chunk_count=chunk_count, error_message=error_message)
        )
