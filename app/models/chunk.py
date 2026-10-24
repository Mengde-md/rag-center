from typing import Any
from uuid import UUID

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import ForeignKeyConstraint, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import get_settings
from app.db.base import Base, CreatedAtMixin
from app.utils.id_generator import generate_id


class Chunk(CreatedAtMixin, Base):
    __tablename__ = "chunks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "kb_id", "document_id"],
            ["documents.tenant_id", "documents.kb_id", "documents.id"],
            ondelete="CASCADE",
        ),
        Index("ix_chunks_tenant_kb", "tenant_id", "kb_id"),
        Index("ix_chunks_document_id", "document_id"),
        Index(
            "ix_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=generate_id)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    kb_id: Mapped[UUID] = mapped_column(nullable=False)
    document_id: Mapped[UUID] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # DeclarativeBase.metadata is reserved; the physical PostgreSQL column is still 'metadata'.
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        VECTOR(get_settings().embedding_dimensions), nullable=False
    )
