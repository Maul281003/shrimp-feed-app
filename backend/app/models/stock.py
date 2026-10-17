import uuid
from sqlalchemy import Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class FeedStock(Base, TimestampMixin):
    __tablename__ = "feed_stocks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    min_threshold_kg: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)