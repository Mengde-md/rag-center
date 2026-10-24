from fastapi import APIRouter

from app.api.dependencies import KnowledgeBaseServiceDep
from app.schemas.common import ResponseEnvelope
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseCreated

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge bases"])


@router.post("/create", response_model=ResponseEnvelope[KnowledgeBaseCreated])
async def create_knowledge_base(
    body: KnowledgeBaseCreate, service: KnowledgeBaseServiceDep
) -> ResponseEnvelope[KnowledgeBaseCreated]:
    return ResponseEnvelope(data=await service.create(body))
