from fastapi import APIRouter, status
from app.api.dependencies import UoWDep, MemoryServiceDep
from app.api.schemas import TurnRequest, TurnResponse

router = APIRouter(prefix="/turns", tags=["turns"])

@router.post("", response_model=TurnResponse, status_code=status.HTTP_201_CREATED)
async def create_turn(
    data: TurnRequest,
    uow: UoWDep,
    memory_service: MemoryServiceDep,
) -> TurnResponse:
    turn = await memory_service.ingest_turn(uow, data)
    return TurnResponse(id=str(turn.id))
