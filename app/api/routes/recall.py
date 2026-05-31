from fastapi import APIRouter
from app.api.dependencies import UoWDep, RecallServiceDep
from app.api.schemas.recall import RecallRequest, RecallResponse

router = APIRouter(tags=["recall"])


@router.post("/recall", response_model=RecallResponse)
async def recall(data: RecallRequest, uow: UoWDep, recall_service: RecallServiceDep):
    return await recall_service.recall(uow, data.query, data.user_id, data.max_tokens)
