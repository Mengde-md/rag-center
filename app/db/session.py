from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_database(url: str) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(url, pool_pre_ping=True, hide_parameters=True)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def verify_database(engine: AsyncEngine, dimensions: int) -> None:
    async with engine.connect() as connection:
        actual = await connection.scalar(
            text(
                "SELECT format_type(atttypid, atttypmod) FROM pg_attribute "
                "WHERE attrelid = to_regclass('chunks') AND attname = 'embedding'"
            )
        )
        if actual is None:
            raise RuntimeError("Database schema missing; run alembic upgrade head")
        if actual != f"vector({dimensions})":
            raise RuntimeError(
                "EMBEDDING_DIMENSIONS differs from the database; migrate and re-index first"
            )
