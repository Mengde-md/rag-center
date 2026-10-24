from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class IndexedChunk:
    chunk_id: UUID
    tenant_id: str
    kb_id: UUID
    document_id: UUID
    title: str
    content: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchHit:
    document_id: UUID
    chunk_id: UUID
    title: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Implementation identifier for logs and response metadata."""

    @abstractmethod
    async def add_chunks(self, chunks: list[IndexedChunk]) -> None:
        """Write chunk vectors and metadata without committing the caller's transaction."""

    @abstractmethod
    async def similarity_search(
        self,
        query_vector: list[float],
        *,
        tenant_id: str,
        kb_id: UUID,
        top_k: int = 5,
    ) -> list[SearchHit]:
        """Return scoped hits in descending relevance order."""

    @abstractmethod
    async def delete_by_document_id(self, document_id: UUID, *, tenant_id: str) -> None:
        """Delete a document's vectors with explicit tenant scope."""
