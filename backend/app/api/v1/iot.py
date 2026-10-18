from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.device import Device, DeviceStatus
from app.models.command import DeviceCommand

router = APIRouter()

@router.post("/heartbeat")
async def device_heartbeat(serial: str, db: AsyncSession = Depends(get_db)):
    device = (await db.execute(select(Device).where(Device.serial == serial))).scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device tidak terdaftar di sistem")
    
    device.status = DeviceStatus.ONLINE
    device.last_seen_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "ok", "message": "Heartbeat received"}

@router.get("/command")
async def get_command(serial: str, db: AsyncSession = Depends(get_db)):
    device = (await db.execute(select(Device).where(Device.serial == serial))).scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device tidak dikenal")
        
    # Cari perintah yang belum dieksekusi
    cmd = (await db.execute(
        select(DeviceCommand)
        .where(DeviceCommand.device_id == device.id, DeviceCommand.is_executed == False)
        .order_by(DeviceCommand.created_at.asc())
    )).scalars().first()

    if cmd:
        # KUNCI PERBAIKAN: Tandai perintah sudah diambil agar tidak diulang terus
        cmd.is_executed = True
        await db.commit()
        return {"command": cmd.command_type, "id": cmd.id}
        
    return {"command": None}