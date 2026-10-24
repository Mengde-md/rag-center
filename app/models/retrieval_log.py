from typing import Any
from uuid import UUID

from sqlalchemy import Float, ForeignKeyConstraint, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin
from app.utils.id_generator import generate_id


class RetrievalLog(CreatedAtMixin, Base):
    __tablename__ = "retrieval_logs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "kb_id"],
            ["knowledge_bases.tenant_id", "knowledge_bases.id"],
            ondelete="CASCADE",
        ),
        Index("ix_retrieval_logs_tenant_kb", "tenant_id", "kb_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=generate_id)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    kb_id: Mapped[UUID] = mapped_column(nullable=False)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_chunks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_store: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
