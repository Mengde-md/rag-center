from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.api.v1.router import router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.session import create_database, verify_database
from app.providers.embedding.openai_compatible import OpenAICompatibleEmbeddingProvider


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging(config.log_level)
        engine, session_factory = create_database(config.database_url)
        app.state.session_factory = session_factory
        try:
            await verify_database(engine, config.embedding_dimensions)
            async with httpx.AsyncClient(timeout=config.model_timeout_seconds) as client:
                app.state.embedding_provider = OpenAICompatibleEmbeddingProvider(client, config)
                yield
        finally:
            await engine.dispose()

    app = FastAPI(title="RAG Center", version="0.1.0", lifespan=lifespan)
    app.state.settings = config
    register_exception_handlers(app)
    app.include_router(router)
    return app


app = create_app()
