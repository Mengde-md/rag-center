from time import perf_counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.embedding.base import EmbeddingProvider
from app.providers.vectorstores.base import VectorStore
from app.repositories.retrieval_log_repository import RetrievalLogRepository
from app.schemas.rag import RetrievalMetadata, RetrievalRequest, RetrievalResult, RetrievedChunk
from app.services.knowledge_base_service import KnowledgeBaseService
from app.utils.id_generator import generate_id


class RagService:
    def __init__(
        self,
        session: AsyncSession,
        knowledge_bases: KnowledgeBaseService,
        embedding: EmbeddingProvider,
        vector_store: VectorStore,
        logs: RetrievalLogRepository,
        top_k: int,
    ):
        self.session = session
        self.knowledge_bases = knowledge_bases
        self.embedding = embedding
        self.vector_store = vector_store
        self.logs = logs
        self.top_k = top_k

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        started = perf_counter()
        log_id = generate_id()
        await self.knowledge_bases.require(request.tenant_id, request.kb_id)
        # Return the read connection to the pool during the model request.
        await self.session.rollback()
        vector = await self.embedding.embed_query(request.query)
        hits = await self.vector_store.similarity_search(
            vector, tenant_id=request.tenant_id, kb_id=request.kb_id, top_k=self.top_k
        )
        result = RetrievalResult(
            query=request.query,
            kb_id=request.kb_id,
            retrieved_chunks=[
                RetrievedChunk(
                    document_id=hit.document_id,
                    chunk_id=hit.chunk_id,
                    title=hit.title,
                    content=hit.content,
                    score=hit.score,
                    metadata=hit.metadata,
                )
                for hit in hits
            ],
            metadata=RetrievalMetadata(
                retrieval_log_id=log_id, top_k=self.top_k, vector_store=self.vector_store.name
            ),
        )
        await self.logs.create(request, result, latency_ms=(perf_counter() - started) * 1000)
        await self.session.commit()
        return result
