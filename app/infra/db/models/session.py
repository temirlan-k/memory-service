from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.models import Base

if TYPE_CHECKING:
    from app.infra.db.models.memory import Memory
    from app.infra.db.models.turn import Turn


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    turns: Mapped[list["Turn"]] = relationship(back_populates="session", passive_deletes=True)
    memories: Mapped[list["Memory"]] = relationship(back_populates="source_session", passive_deletes=True)