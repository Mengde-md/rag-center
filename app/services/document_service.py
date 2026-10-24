import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, EmbeddingError
from app.models.document import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentUpload, DocumentUploaded
from app.services.indexing_service import IndexingService
from app.services.knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(
        self,
        session: AsyncSession,
        repository: DocumentRepository,
        knowledge_bases: KnowledgeBaseService,
        indexing: IndexingService,
        max_content_length: int,
    ):
        self.session = session
        self.repository = repository
        self.knowledge_bases = knowledge_bases
        self.indexing = indexing
        self.max_content_length = max_content_length

    async def upload(self, request: DocumentUpload) -> DocumentUploaded:
        if len(request.content) > self.max_content_length:
            raise AppError(41301, "document exceeds MAX_CONTENT_LENGTH", 413)
        await self.knowledge_bases.require(request.tenant_id, request.kb_id)
        document = await self.repository.create(request.tenant_id, request.kb_id, request.title)
        document_id = document.id
        # Commit PROCESSING before the external call, so a failed index still has a durable record.
        await self.session.commit()
        try:
            count = await self.indexing.index_document(
                document_id=document_id,
                tenant_id=request.tenant_id,
                kb_id=request.kb_id,
                title=request.title,
                content=request.content,
            )
            await self.repository.set_status(
                document_id,
                tenant_id=request.tenant_id,
                status=DocumentStatus.SUCCESS,
                chunk_count=count,
            )
            # The PgVectorStore insert and SUCCESS transition are atomic.
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            message = exc.msg if isinstance(exc, EmbeddingError) else "document indexing failed"
            logger.warning(
                "Indexing failed document_id=%s error=%s", document_id, type(exc).__name__
            )
            await self.repository.set_status(
                document_id,
                tenant_id=request.tenant_id,
                status=DocumentStatus.FAILED,
                error_message=message,
            )
            await self.session.commit()
            raise AppError(
                50202 if isinstance(exc, EmbeddingError) else 50002,
                message,
                502 if isinstance(exc, EmbeddingError) else 500,
                data={"document_id": str(document_id), "status": 2, "chunk_count": 0},
            ) from exc

        return DocumentUploaded(
            document_id=document_id,
            kb_id=request.kb_id,
            status=DocumentStatus.SUCCESS,
            chunk_count=count,
        )
