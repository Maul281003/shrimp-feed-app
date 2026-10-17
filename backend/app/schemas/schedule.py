import uuid
from pydantic import BaseModel, Field

class ScheduleCreate(BaseModel):
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    motor_duration_sec: int = Field(default=4, ge=1, le=30)
    blower_duration_sec: int = Field(default=2, ge=0, le=10)

class ScheduleOut(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    order_index: int
    hour: int
    minute: int
    motor_duration_sec: int
    blower_duration_sec: int
    is_enabled: bool

    class Config:
        from_attributes = True

class ScheduleUpdate(BaseModel):
    is_enabled: bool