import uuid
import enum
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text, Float, Boolean, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.models import Base

if TYPE_CHECKING:
    from app.infra.db.models.session import Session
    from app.infra.db.models.turn import Turn


class MemoryType(str, enum.Enum):
    fact = "fact"
    preference = "preference"
    opinion = "opinion"
    event = "event"

class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    source_session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id", ondelete="CASCADE"))
    source_turn_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("turns.id", ondelete="CASCADE"))

    type: Mapped[str] = mapped_column(String, nullable=False)
    key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    embedding: Mapped[list | None] = mapped_column(Vector(1536), nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("memories.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    source_session: Mapped["Session"] = relationship(back_populates="memories")
    source_turn: Mapped["Turn"] = relationship(back_populates="memories")
    supersedes: Mapped["Memory | None"] = relationship("Memory", foreign_keys="Memory.supersedes_id", remote_side="Memory.id",)

    __table_args__ = (
        Index("ix_memories_user_key_active", "user_id", "key", "active"),
    )