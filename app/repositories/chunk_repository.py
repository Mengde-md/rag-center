from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.providers.vectorstores.base import IndexedChunk, SearchHit


class ChunkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_many(self, chunks: list[IndexedChunk]) -> None:
        self.session.add_all(
            [
                Chunk(
                    id=chunk.chunk_id,
                    tenant_id=chunk.tenant_id,
                    kb_id=chunk.kb_id,
                    document_id=chunk.document_id,
                    title=chunk.title,
                    content=chunk.content,
                    chunk_metadata=chunk.metadata,
                    embedding=chunk.embedding,
                )
                for chunk in chunks
            ]
        )
        await self.session.flush()

    async def similarity_search(
        self, query_vector: list[float], *, tenant_id: str, kb_id: UUID, top_k: int
    ) -> list[SearchHit]:
        # pgvector >= 0.8.0 expands HNSW scanning when tenant/KB filters discard candidates.
        await self.session.execute(text("SET LOCAL hnsw.iterative_scan = 'strict_order'"))
        distance = Chunk.embedding.cosine_distance(query_vector)
        rows = await self.session.execute(
            select(Chunk, (1 - distance).label("score"))
            .join(Document, Chunk.document_id == Document.id)
            .where(
                Chunk.tenant_id == tenant_id,
                Chunk.kb_id == kb_id,
                Document.status == DocumentStatus.SUCCESS,
            )
            .order_by(distance)
            .limit(top_k)
        )
        return [
            SearchHit(
                document_id=chunk.document_id,
                chunk_id=chunk.id,
                title=chunk.title,
                content=chunk.content,
                score=max(-1.0, min(1.0, float(score))),
                metadata=chunk.chunk_metadata,
            )
            for chunk, score in rows
        ]

    async def delete_by_document_id(self, document_id: UUID, *, tenant_id: str) -> None:
        await self.session.execute(
            delete(Chunk).where(Chunk.document_id == document_id, Chunk.tenant_id == tenant_id)
        )
