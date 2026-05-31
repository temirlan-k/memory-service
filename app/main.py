from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.api.exceptions import register_exception_handlers
from app.api.routes import turns, healthchecks, memories, recall, search
from config.logging import setup_logging
from app.infra.db.get_db import DatabaseAdapter
from config import db_settings

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log.info("starting_up")
    app.state.db = DatabaseAdapter(db_settings)
    yield
    log.info("shutting_down")
    await app.state.db.close()


app = FastAPI(title="Memory Service", lifespan=lifespan)


register_exception_handlers(app)

app.include_router(turns.router)
app.include_router(healthchecks.router)
app.include_router(memories.router)
app.include_router(recall.router)
app.include_router(search.router)
