import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Uuid, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class DeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNPAIRED = "unpaired"
    UNKNOWN = "unknown"


class StockStatus(str, enum.Enum):
    FULL = "full"
    LOW = "low"
    EMPTY = "empty"
    UNKNOWN = "unknown"


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    serial: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Kolom baru untuk stok di dalam bak penampungan (Hopper)
    hopper_stock_kg: Mapped[float] = mapped_column(Float, default=15.0, nullable=False)
    max_hopper_kg: Mapped[float] = mapped_column(Float, default=25.0, nullable=False)

    gateway_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("gateways.id", ondelete="SET NULL"), nullable=True, index=True
    )
    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("farms.id", ondelete="SET NULL"), nullable=True, index=True
    )
    paired_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    paired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[DeviceStatus] = mapped_column(
        SAEnum(DeviceStatus, name="device_status"), default=DeviceStatus.UNPAIRED, nullable=False
    )
    stock_status: Mapped[StockStatus] = mapped_column(
        SAEnum(StockStatus, name="stock_status"), default=StockStatus.UNKNOWN, nullable=False
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # BAGIAN YANG DIPERBAIKI (Tanda kutip penutup)
    gateway: Mapped["Gateway | None"] = relationship("Gateway", back_populates="devices")
    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="device", cascade="all, delete-orphan")