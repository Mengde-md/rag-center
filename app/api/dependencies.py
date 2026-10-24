from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.providers.embedding.base import EmbeddingProvider
from app.providers.parsers.plain_text import PlainTextParser
from app.providers.vectorstores.base import VectorStore
from app.providers.vectorstores.pgvector import PgVectorStore
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.retrieval_log_repository import RetrievalLogRepository
from app.services.document_service import DocumentService
from app.services.indexing_service import IndexingService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.rag_service import RagService
from app.utils.text_splitter import CharacterTextSplitter


def get_config(request: Request) -> Settings:
    return request.app.state.settings


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        try:
            yield session
        finally:
            # Repositories flush only. Services own successful/failure transaction boundaries.
            await session.rollback()


def get_embedding(request: Request) -> EmbeddingProvider:
    return request.app.state.embedding_provider


SessionDep = Annotated[AsyncSession, Depends(get_session)]
ConfigDep = Annotated[Settings, Depends(get_config)]
EmbeddingDep = Annotated[EmbeddingProvider, Depends(get_embedding)]


def get_vector_store(session: SessionDep, config: ConfigDep) -> VectorStore:
    # Composition root: register new implementations here; services depend only on VectorStore.
    if config.vector_store == "pgvector":
        return PgVectorStore(ChunkRepository(session))
    raise ValueError(f"unsupported VECTOR_STORE: {config.vector_store}")


VectorStoreDep = Annotated[VectorStore, Depends(get_vector_store)]


def get_knowledge_base_service(session: SessionDep) -> KnowledgeBaseService:
    return KnowledgeBaseService(session, KnowledgeBaseRepository(session))


KnowledgeBaseServiceDep = Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)]


def get_document_service(
    session: SessionDep,
    config: ConfigDep,
    embedding: EmbeddingDep,
    vector_store: VectorStoreDep,
    knowledge_bases: KnowledgeBaseServiceDep,
) -> DocumentService:
    indexing = IndexingService(
        PlainTextParser(),
        CharacterTextSplitter(config.chunk_size, config.chunk_overlap),
        embedding,
        vector_store,
    )
    return DocumentService(
        session, DocumentRepository(session), knowledge_bases, indexing, config.max_content_length
    )


def get_rag_service(
    session: SessionDep,
    config: ConfigDep,
    embedding: EmbeddingDep,
    vector_store: VectorStoreDep,
    knowledge_bases: KnowledgeBaseServiceDep,
) -> RagService:
    return RagService(
        session,
        knowledge_bases,
        embedding,
        vector_store,
        RetrievalLogRepository(session),
        config.top_k,
    )
