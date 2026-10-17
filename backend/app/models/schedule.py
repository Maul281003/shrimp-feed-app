import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Schedule(Base, TimestampMixin):
    __tablename__ = "schedules"
    __table_args__ = (UniqueConstraint("device_id", "order_index", name="uq_device_slot"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 0..7
    hour: Mapped[int] = mapped_column(Integer, nullable=False)
    minute: Mapped[int] = mapped_column(Integer, nullable=False)
    motor_duration_sec: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    blower_duration_sec: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    device: Mapped["Device"] = relationship("Device", back_populates="schedules")  # noqa: F821