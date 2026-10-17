import enum
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, Float, JSON, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class LogEventType(str, enum.Enum):
    SCHEDULED_FEED = "scheduled_feed"
    MANUAL_FEED = "manual_feed"
    STOCK_LOW = "stock_low"
    HEARTBEAT = "heartbeat"
    STATUS_CHANGE = "status_change"

class LogSource(str, enum.Enum):
    DEVICE = "device"
    APP = "app"
    SYSTEM = "system"

class Log(Base):
    __tablename__ = "logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[LogEventType] = mapped_column(SAEnum(LogEventType, name="log_event_type"), nullable=False)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    amount_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[LogSource] = mapped_column(SAEnum(LogSource, name="log_source"), default=LogSource.DEVICE, nullable=False)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)