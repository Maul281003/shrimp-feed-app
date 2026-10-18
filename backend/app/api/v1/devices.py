import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_farm_access
from app.core.database import get_db
from app.models.device import Device, DeviceStatus
from app.models.gateway import Gateway, GatewayStatus
from app.models.user import User
from app.models.log import Log, LogEventType, LogSource
from app.schemas.device import DeviceOut, DevicePairIn, GatewayCreate, GatewayOut, DeviceUpdate, DeviceRefill
from app.models.command import DeviceCommand

router = APIRouter()

# ---------- Gateways ----------
@router.get("/gateways", response_model=list[GatewayOut])
async def list_gateways(farm_id: uuid.UUID = Query(...), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_farm_access(farm_id, user, db)
    return (await db.execute(select(Gateway).where(Gateway.farm_id == farm_id))).scalars().all()

@router.post("/gateways", response_model=GatewayOut, status_code=201)
async def create_gateway(payload: GatewayCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_farm_access(payload.farm_id, user, db, write=True)
    if (await db.execute(select(Gateway).where(Gateway.serial == payload.serial))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Serial gateway sudah dipakai")
    gw = Gateway(**payload.model_dump())
    db.add(gw)
    await db.commit()
    await db.refresh(gw)
    return gw

# ---------- Devices ----------
@router.get("/devices", response_model=list[DeviceOut])
async def list_devices(farm_id: uuid.UUID = Query(...), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_farm_access(farm_id, user, db)
    return (await db.execute(select(Device).where(Device.farm_id == farm_id))).scalars().all()

@router.get("/devices/{device_id}", response_model=DeviceOut)
async def get_device(device_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device or not device.farm_id: raise HTTPException(status_code=404, detail="Alat tidak ditemukan")
    await require_farm_access(device.farm_id, user, db)
    return device

@router.patch("/devices/{device_id}", response_model=DeviceOut)
async def update_device(device_id: uuid.UUID, payload: DeviceUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device or not device.farm_id: raise HTTPException(status_code=404, detail="Alat tidak ditemukan")
    await require_farm_access(device.farm_id, user, db, write=True)
    device.name = payload.name
    await db.commit()
    await db.refresh(device)
    return device

@router.post("/devices/{device_id}/refill", response_model=DeviceOut)
async def refill_hopper(device_id: uuid.UUID, payload: DeviceRefill, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device or not device.farm_id: raise HTTPException(status_code=404, detail="Alat tidak ditemukan")
    await require_farm_access(device.farm_id, user, db, write=True)
    
    device.hopper_stock_kg += payload.amount_kg
    if device.hopper_stock_kg > device.max_hopper_kg:
        device.hopper_stock_kg = device.max_hopper_kg
        
    await db.commit()
    await db.refresh(device)
    return device

@router.post("/devices/pair", response_model=DeviceOut, status_code=201)
async def pair_device(payload: DevicePairIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    gw = await db.get(Gateway, payload.gateway_id)
    if not gw: raise HTTPException(status_code=404, detail="Gateway tidak ditemukan")
    _, role = await require_farm_access(gw.farm_id, user, db, write=True)
    if role == "viewer": raise HTTPException(status_code=403, detail="Akses hanya baca")
    
    device = (await db.execute(select(Device).where(Device.serial == payload.serial))).scalar_one_or_none()
    if not device: raise HTTPException(status_code=404, detail="Serial alat tidak dikenal")
    
    # Cek apakah sudah punya farm_id (sudah menempati tambak lain)
    if device.farm_id is not None: 
        raise HTTPException(status_code=409, detail="Alat sudah terdaftar di akun lain")
    
    device.gateway_id = gw.id
    device.farm_id = gw.farm_id
    device.paired_by_id = user.id
    device.paired_at = datetime.now(timezone.utc)
    device.status = DeviceStatus.ONLINE 
    
    if payload.name: device.name = payload.name
    await db.commit()
    await db.refresh(device)
    return device

@router.post("/devices/{device_id}/unpair", response_model=DeviceOut)
async def unpair_device(device_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device or not device.farm_id: raise HTTPException(status_code=404, detail="Alat tidak ditemukan")
    await require_farm_access(device.farm_id, user, db, write=True)
    
    device.gateway_id = None
    device.farm_id = None
    device.paired_by_id = None
    device.paired_at = None
    device.status = DeviceStatus.UNPAIRED
    await db.commit()
    await db.refresh(device)
    return device

# ---------- Simulasi ----------
@router.post("/devices/{device_id}/simulate-heartbeat", response_model=DeviceOut)
async def simulate_heartbeat(device_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device or not device.farm_id: raise HTTPException(status_code=404, detail="Alat tidak ditemukan")
    await require_farm_access(device.farm_id, user, db)
    device.status = DeviceStatus.ONLINE
    device.last_seen_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(device)
    return device

# ---------- Manual Feed (Diperbarui dengan Durasi) ----------
@router.post("/devices/{device_id}/feed", response_model=DeviceOut)
async def manual_feed(device_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device or not device.farm_id: raise HTTPException(status_code=404, detail="Alat tidak ditemukan")
    await require_farm_access(device.farm_id, user, db, write=True)
    
    # Cek stok minimal
    if device.hopper_stock_kg <= 0:
        raise HTTPException(400, "Stok di bak alat ini habis. Isi ulang dulu!")
        
    # Masukkan perintah ke antrean dengan durasi default
    new_cmd = DeviceCommand(
        device_id=device.id, 
        command_type="feed_now",
        duration_motor=4,   # Default 4 detik
        duration_blower=2   # Default 2 detik
    )
    db.add(new_cmd)
    
    await db.commit()
    await db.refresh(device)
    return device