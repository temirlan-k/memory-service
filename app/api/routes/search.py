from fastapi import APIRouter
from app.api.dependencies import UoWDep, SearchServiceDep
from app.api.schemas.search import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(data: SearchRequest, uow: UoWDep, search_service: SearchServiceDep):
    return await search_service.search(uow, data.query, data.user_id, data.limit)
