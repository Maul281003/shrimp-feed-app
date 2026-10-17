import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.device import DeviceStatus, StockStatus
from app.models.gateway import GatewayStatus

class GatewayCreate(BaseModel):
    farm_id: uuid.UUID
    serial: str = Field(min_length=4)
    name: str = Field(min_length=1)

class GatewayOut(BaseModel):
    id: uuid.UUID
    farm_id: uuid.UUID
    serial: str
    name: str
    status: GatewayStatus
    last_seen_at: datetime | None

    class Config:
        from_attributes = True

class DeviceOut(BaseModel):
    id: uuid.UUID
    serial: str
    name: str | None
    gateway_id: uuid.UUID | None
    farm_id: uuid.UUID | None
    status: DeviceStatus
    stock_status: StockStatus
    last_seen_at: datetime | None
    paired_at: datetime | None
    hopper_stock_kg: float # <-- Tambahan
    max_hopper_kg: float   # <-- Tambahan

    class Config:
        from_attributes = True

class DevicePairIn(BaseModel):
    serial: str = Field(min_length=4)
    gateway_id: uuid.UUID
    name: str | None = None

class DeviceUpdate(BaseModel):
    name: str = Field(min_length=1)

# Schema baru untuk Refill (Isi Ulang Bak)
class DeviceRefill(BaseModel):
    amount_kg: float = Field(gt=0)