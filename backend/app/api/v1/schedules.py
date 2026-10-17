import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_farm_access
from app.core.database import get_db
from app.models.device import Device
from app.models.schedule import Schedule
from app.models.user import User
from app.schemas.schedule import ScheduleCreate, ScheduleOut, ScheduleUpdate

router = APIRouter()

@router.get("/devices/{device_id}/schedules", response_model=list[ScheduleOut])
async def list_schedules(device_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device or not device.farm_id: raise HTTPException(404, "Alat tidak ditemukan")
    await require_farm_access(device.farm_id, user, db)
    return (await db.execute(select(Schedule).where(Schedule.device_id == device_id).order_by(Schedule.order_index))).scalars().all()

@router.post("/devices/{device_id}/schedules", response_model=ScheduleOut, status_code=201)
async def add_schedule(device_id: uuid.UUID, payload: ScheduleCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device or not device.farm_id: raise HTTPException(404, "Alat tidak ditemukan")
    await require_farm_access(device.farm_id, user, db, write=True)
    
    existing_schedules = (await db.execute(select(Schedule).where(Schedule.device_id == device_id))).scalars().all()
    if len(existing_schedules) >= 8: raise HTTPException(400, "Maksimal 8 jadwal per alat")
        
    used_indices = [s.order_index for s in existing_schedules]
    next_index = 0
    while next_index in used_indices: next_index += 1

    schedule = Schedule(device_id=device_id, order_index=next_index, **payload.model_dump())
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule

@router.patch("/schedules/{schedule_id}", response_model=ScheduleOut)
async def toggle_schedule(schedule_id: uuid.UUID, payload: ScheduleUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    schedule = await db.get(Schedule, schedule_id)
    if not schedule: raise HTTPException(404, "Jadwal tidak ditemukan")
    device = await db.get(Device, schedule.device_id)
    await require_farm_access(device.farm_id, user, db, write=True)
    
    schedule.is_enabled = payload.is_enabled
    await db.commit()
    await db.refresh(schedule)
    return schedule

@router.delete("/schedules/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    schedule = await db.get(Schedule, schedule_id)
    if not schedule: raise HTTPException(404, "Jadwal tidak ditemukan")
    device = await db.get(Device, schedule.device_id)
    await require_farm_access(device.farm_id, user, db, write=True)
    await db.delete(schedule)
    await db.commit()