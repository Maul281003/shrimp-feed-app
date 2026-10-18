import uuid
from sqlalchemy import String, ForeignKey, Uuid, Boolean, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    command_type: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_motor: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    duration_blower: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    is_executed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)