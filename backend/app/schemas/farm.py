import uuid
from pydantic import BaseModel, Field


class FarmCreate(BaseModel):
    name: str = Field(min_length=2)
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class FarmOut(BaseModel):
    id: uuid.UUID
    name: str
    location: str | None
    latitude: float | None
    longitude: float | None
    role: str  # owner | technician | viewer

    class Config:
        from_attributes = True