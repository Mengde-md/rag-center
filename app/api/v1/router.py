from fastapi import APIRouter

from app.api.v1.routes import documents, knowledge_bases, rag
from app.schemas.common import ResponseEnvelope

router = APIRouter(
    prefix="/api/v1",
    responses={
        status: {"model": ResponseEnvelope[object], "description": "Unified error response"}
        for status in (404, 413, 422, 500, 502)
    },
)
router.include_router(knowledge_bases.router)
router.include_router(documents.router)
router.include_router(rag.router)
