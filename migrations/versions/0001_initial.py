"""Create knowledge bases, documents, chunks, and retrieval logs.

Revision ID: 0001
Revises:

EMBEDDING_DIMENSIONS is an installation-time parameter for this initial migration.
Once installed, dimension changes need a new migration and a complete re-index.
"""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import VECTOR
from sqlalchemy.dialects import postgresql

from app.core.config import get_settings

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def timestamps(*, updated: bool = True) -> list[sa.Column]:
    columns = [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        )
    ]
    if updated:
        columns.append(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            )
        )
    return columns


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "knowledge_bases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_knowledge_bases"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_knowledge_bases_tenant_id_id"),
    )
    op.create_index("ix_knowledge_bases_tenant_id", "knowledge_bases", ["tenant_id"])

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("kb_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text()),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_documents"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "kb_id"],
            ["knowledge_bases.tenant_id", "knowledge_bases.id"],
            name="fk_documents_tenant_id_knowledge_bases",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("tenant_id", "kb_id", "id", name="uq_documents_tenant_kb_id"),
        sa.CheckConstraint("status IN (1, 2, 3)", name=op.f("ck_documents_status")),
        sa.CheckConstraint("chunk_count >= 0", name=op.f("ck_documents_chunk_count")),
    )
    op.create_index("ix_documents_tenant_kb", "documents", ["tenant_id", "kb_id"])

    op.create_table(
        "chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("kb_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False),
        sa.Column("embedding", VECTOR(get_settings().embedding_dimensions), nullable=False),
        *timestamps(updated=False),
        sa.PrimaryKeyConstraint("id", name="pk_chunks"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "kb_id", "document_id"],
            ["documents.tenant_id", "documents.kb_id", "documents.id"],
            name="fk_chunks_tenant_id_documents",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_chunks_tenant_kb", "chunks", ["tenant_id", "kb_id"])
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])
    op.create_index(
        "ix_chunks_embedding_hnsw",
        "chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.create_table(
        "retrieval_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("kb_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("retrieved_chunks", postgresql.JSONB(), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("vector_store", sa.String(32), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        *timestamps(updated=False),
        sa.PrimaryKeyConstraint("id", name="pk_retrieval_logs"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "kb_id"],
            ["knowledge_bases.tenant_id", "knowledge_bases.id"],
            name="fk_retrieval_logs_tenant_id_knowledge_bases",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_retrieval_logs_tenant_kb", "retrieval_logs", ["tenant_id", "kb_id"])


def downgrade() -> None:
    op.drop_table("retrieval_logs")
    op.drop_table("chunks")
    op.drop_table("documents")
    op.drop_table("knowledge_bases")
    # The extension may be used by other schemas; leave it installed.
