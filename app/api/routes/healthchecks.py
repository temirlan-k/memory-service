from typing import Annotated
from fastapi import APIRouter, Depends

from app.api.dependencies import get_db_adapter
from app.infra.db.get_db import DatabaseAdapter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check(
    db: Annotated[DatabaseAdapter, Depends(get_db_adapter)],
) -> dict:
    healthy = await db.healthcheck()
    return {"status": "ready" if healthy else "unavailable"}
