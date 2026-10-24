from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_rag_service
from app.schemas.common import ResponseEnvelope
from app.schemas.rag import RetrievalRequest, RetrievalResult
from app.services.rag_service import RagService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/retrieve", response_model=ResponseEnvelope[RetrievalResult])
async def retrieve(
    body: RetrievalRequest, service: Annotated[RagService, Depends(get_rag_service)]
) -> ResponseEnvelope[RetrievalResult]:
    return ResponseEnvelope(data=await service.retrieve(body))
