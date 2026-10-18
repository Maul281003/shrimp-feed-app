import uuid
from pydantic import BaseModel

class ScheduleCreate(BaseModel):
    hour: int
    minute: int
    motor_duration_sec: int
    blower_duration_sec: int

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