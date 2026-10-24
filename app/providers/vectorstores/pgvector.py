from uuid import UUID

from app.providers.vectorstores.base import IndexedChunk, SearchHit, VectorStore
from app.repositories.chunk_repository import ChunkRepository


class PgVectorStore(VectorStore):
    def __init__(self, chunks: ChunkRepository):
        self.chunks = chunks

    @property
    def name(self) -> str:
        return "pgvector"

    async def add_chunks(self, chunks: list[IndexedChunk]) -> None:
        await self.chunks.add_many(chunks)

    async def similarity_search(
        self,
        query_vector: list[float],
        *,
        tenant_id: str,
        kb_id: UUID,
        top_k: int = 5,
    ) -> list[SearchHit]:
        return await self.chunks.similarity_search(
            query_vector, tenant_id=tenant_id, kb_id=kb_id, top_k=top_k
        )

    async def delete_by_document_id(self, document_id: UUID, *, tenant_id: str) -> None:
        await self.chunks.delete_by_document_id(document_id, tenant_id=tenant_id)
