from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.models.device import Device, DeviceStatus
from app.models.command import DeviceCommand
from app.models.log import Log, LogEventType, LogSource

router = APIRouter()

# --- RUTE BARU UNTUK CEK JAM SERVER ---
@router.get("/time")
async def get_server_time():
    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)
    return {
        "server_time_wib": now.strftime("%Y-%m-%d %H:%M:%S"),
        "jam": now.hour,
        "menit": now.minute
    }

@router.post("/heartbeat")
async def device_heartbeat(serial: str, db: AsyncSession = Depends(get_db)):
    device = (await db.execute(select(Device).where(Device.serial == serial))).scalar_one_or_none()
    if not device: raise HTTPException(404, "Device tidak terdaftar")
    if device.farm_id is None: return {"status": "error", "message": "Belum di-pair"}
    
    device.status = DeviceStatus.ONLINE
    device.last_seen_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "ok"}

@router.get("/command")
async def get_command(serial: str, db: AsyncSession = Depends(get_db)):
    device = (await db.execute(select(Device).where(Device.serial == serial))).scalar_one_or_none()
    if not device: raise HTTPException(404, "Device tidak dikenal")
        
    cmd = (await db.execute(
        select(DeviceCommand)
        .where(DeviceCommand.device_id == device.id, DeviceCommand.is_executed == False)
        .order_by(DeviceCommand.created_at.asc())
    )).scalars().first()

    if cmd:
        cmd.is_executed = True
        
        amount = cmd.duration_motor * 0.5
        if device.hopper_stock_kg >= amount:
            device.hopper_stock_kg -= amount
        else:
            device.hopper_stock_kg = 0
            
        new_log = Log(
            device_id=device.id, 
            event_type=LogEventType.MANUAL_FEED, 
            event_at=datetime.now(timezone.utc), 
            duration_sec=cmd.duration_motor, 
            amount_kg=amount, 
            source=LogSource.DEVICE
        )
        db.add(new_log)
        await db.commit()
        
        return {
            "command": cmd.command_type, 
            "id": cmd.id,
            "duration_motor": cmd.duration_motor,
            "duration_blower": cmd.duration_blower
        }
        
    return {"command": None}