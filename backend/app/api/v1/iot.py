from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.device import Device, DeviceStatus
from app.models.command import DeviceCommand
from app.models.log import Log, LogEventType, LogSource

router = APIRouter()

@router.post("/heartbeat")
async def device_heartbeat(serial: str, db: AsyncSession = Depends(get_db)):
    device = (await db.execute(select(Device).where(Device.serial == serial))).scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device tidak terdaftar di sistem")
    
    # Jika alat belum di-pair ke tambak, tolak heartbeat
    if device.farm_id is None:
        return {"status": "error", "message": "Device belum di-pair ke tambak manapun"}
    
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
        # 1. Tandai perintah sudah diambil
        cmd.is_executed = True
        
        # 2. Potong stok di bak alat (Hopper) sebesar 2.5 kg
        amount = 2.5
        if device.hopper_stock_kg >= amount:
            device.hopper_stock_kg -= amount
        else:
            device.hopper_stock_kg = 0 # Jaga-jaga agar tidak minus
            
        # 3. Catat ke Riwayat Pakan (Log)
        new_log = Log(
            device_id=device.id, 
            event_type=LogEventType.MANUAL_FEED, 
            event_at=datetime.now(timezone.utc), 
            duration_sec=3, 
            amount_kg=amount, 
            source=LogSource.DEVICE # Berasal dari eksekusi alat
        )
        db.add(new_log)
        
        await db.commit()
        return {"command": cmd.command_type, "id": cmd.id}
        
    return {"command": None}