# models/turn.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.models import Base

if TYPE_CHECKING:
    from app.infra.db.models.memory import Memory
    from app.infra.db.models.session import Session


class Turn(Base):
    __tablename__ = "turns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    messages: Mapped[dict] = mapped_column(JSONB, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["Session"] = relationship(back_populates="turns")
    memories: Mapped[list["Memory"]] = relationship(back_populates="source_turn", passive_deletes=True)