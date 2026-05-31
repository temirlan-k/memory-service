from fastapi import APIRouter, status
from app.api.dependencies import UoWDep, MemoryServiceDep
from app.api.schemas.memory import MemoryListResponse, MemoryResponse

router = APIRouter(tags=["memories"])


@router.get("/users/{user_id}/memories", response_model=MemoryListResponse)
async def get_user_memories(user_id: str, uow: UoWDep, memory_service: MemoryServiceDep):
    memories = await memory_service.get_user_memories(uow, user_id)
    return MemoryListResponse(
        memories=[
            MemoryResponse(
                id=str(m.id),
                type=m.type,
                key=m.key,
                value=m.value,
                confidence=m.confidence,
                source_session=m.source_session_id,
                source_turn=str(m.source_turn_id),
                active=m.active,
                supersedes=str(m.supersedes_id) if m.supersedes_id else None,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in memories
        ]
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, uow: UoWDep, memory_service: MemoryServiceDep):
    await memory_service.delete_session(uow, session_id)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, uow: UoWDep, memory_service: MemoryServiceDep):
    await memory_service.delete_user(uow, user_id)
