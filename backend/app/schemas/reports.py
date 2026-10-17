import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class StockCreate(BaseModel):
    brand_name: str
    quantity_kg: float
    min_threshold_kg: float = 50.0

class StockOut(StockCreate):
    id: uuid.UUID
    farm_id: uuid.UUID
    class Config:
        from_attributes = True

class StockUpdate(BaseModel):
    quantity_kg: float

class SamplingCreate(BaseModel):
    abw_gram: float = Field(gt=0)
    population: int = Field(gt=0)

class LogOut(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    event_type: str
    event_at: datetime
    amount_kg: float | None
    class Config:
        from_attributes = True

class AnalyticsOut(BaseModel):
    total_feed_kg: float
    current_biomass_kg: float
    fcr: float
    last_sampling_date: datetime | None