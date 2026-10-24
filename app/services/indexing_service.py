from uuid import UUID

from app.providers.embedding.base import EmbeddingProvider
from app.providers.parsers.base import DocumentParser
from app.providers.vectorstores.base import IndexedChunk, VectorStore
from app.utils.id_generator import generate_id
from app.utils.text_splitter import TextSplitter


class IndexingService:
    """Synchronous orchestration; a future worker can call this same entry point."""

    def __init__(
        self,
        parser: DocumentParser,
        splitter: TextSplitter,
        embedding: EmbeddingProvider,
        vector_store: VectorStore,
    ):
        self.parser = parser
        self.splitter = splitter
        self.embedding = embedding
        self.vector_store = vector_store

    async def index_document(
        self, *, document_id: UUID, tenant_id: str, kb_id: UUID, title: str, content: str
    ) -> int:
        parsed = self.parser.parse(content)
        pieces = self.splitter.split(parsed.text)
        if not pieces:
            raise ValueError("document contains no indexable chunks")
        vectors = await self.embedding.embed_texts([piece.content for piece in pieces])
        if len(vectors) != len(pieces):
            raise ValueError("embedding provider returned an incorrect vector count")
        chunks = [
            IndexedChunk(
                chunk_id=generate_id(),
                tenant_id=tenant_id,
                kb_id=kb_id,
                document_id=document_id,
                title=title,
                content=piece.content,
                embedding=vector,
                metadata={
                    **parsed.metadata,
                    "chunk_index": piece.index,
                    "start_char": piece.start_char,
                    "end_char": piece.end_char,
                },
            )
            for piece, vector in zip(pieces, vectors, strict=True)
        ]
        await self.vector_store.add_chunks(chunks)
        return len(chunks)
