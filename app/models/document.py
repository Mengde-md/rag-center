from enum import IntEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.utils.id_generator import generate_id


class DocumentStatus(IntEnum):
    SUCCESS = 1
    FAILED = 2
    PROCESSING = 3


class Document(TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "kb_id"],
            ["knowledge_bases.tenant_id", "knowledge_bases.id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "kb_id", "id", name="uq_documents_tenant_kb_id"),
        CheckConstraint("status IN (1, 2, 3)", name="status"),
        CheckConstraint("chunk_count >= 0", name="chunk_count"),
        Index("ix_documents_tenant_kb", "tenant_id", "kb_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=generate_id)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    kb_id: Mapped[UUID] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="text")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=DocumentStatus.PROCESSING)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
