import uuid
from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Sampling(Base):
    __tablename__ = "samplings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)
    abw_gram: Mapped[float] = mapped_column(Float, nullable=False)
    population: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)