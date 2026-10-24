from sqlalchemy.ext.asyncio import AsyncSession

from app.models.retrieval_log import RetrievalLog
from app.schemas.rag import RetrievalRequest, RetrievalResult


class RetrievalLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, request: RetrievalRequest, result: RetrievalResult, latency_ms: float
    ) -> None:
        self.session.add(
            RetrievalLog(
                id=result.metadata.retrieval_log_id,
                tenant_id=request.tenant_id,
                kb_id=request.kb_id,
                user_id=request.user_id,
                query=request.query,
                retrieved_chunks=[
                    chunk.model_dump(mode="json") for chunk in result.retrieved_chunks
                ],
                top_k=result.metadata.top_k,
                vector_store=result.metadata.vector_store,
                latency_ms=latency_ms,
            )
        )
        await self.session.flush()
