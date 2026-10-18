import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_farm_access
from app.core.database import get_db
from app.models.device import Device
from app.models.log import Log, LogEventType, LogSource
from app.models.stock import FeedStock
from app.models.sampling import Sampling
from app.models.user import User
from app.schemas.reports import StockCreate, StockOut, StockUpdate, SamplingCreate, AnalyticsOut, LogOut

router = APIRouter()

@router.get("/farms/{farm_id}/stocks", response_model=list[StockOut])
async def list_stocks(farm_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_farm_access(farm_id, user, db)
    return (await db.execute(select(FeedStock).where(FeedStock.farm_id == farm_id))).scalars().all()

@router.post("/farms/{farm_id}/stocks", response_model=StockOut, status_code=201)
async def add_stock(farm_id: uuid.UUID, payload: StockCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_farm_access(farm_id, user, db, write=True)
    stock = FeedStock(farm_id=farm_id, **payload.model_dump())
    db.add(stock)
    await db.commit()
    await db.refresh(stock)
    return stock

@router.patch("/stocks/{stock_id}", response_model=StockOut)
async def update_stock(stock_id: uuid.UUID, payload: StockUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stock = await db.get(FeedStock, stock_id)
    if not stock: raise HTTPException(404, "Stok tidak ditemukan")
    await require_farm_access(stock.farm_id, user, db, write=True)
    stock.quantity_kg = payload.quantity_kg
    await db.commit()
    await db.refresh(stock)
    return stock

@router.get("/farms/{farm_id}/logs", response_model=list[LogOut])
async def list_logs(farm_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_farm_access(farm_id, user, db)
    res = await db.execute(
        select(Log).join(Device, Log.device_id == Device.id)
        .where(Device.farm_id == farm_id)
        .order_by(Log.event_at.desc()).limit(50)
    )
    return res.scalars().all()

@router.post("/farms/{farm_id}/samplings", status_code=201)
async def add_sampling(farm_id: uuid.UUID, payload: SamplingCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_farm_access(farm_id, user, db, write=True)
    sampling = Sampling(farm_id=farm_id, **payload.model_dump())
    db.add(sampling)
    await db.commit()
    return {"status": "ok"}

@router.get("/farms/{farm_id}/analytics", response_model=AnalyticsOut)
async def get_analytics(farm_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_farm_access(farm_id, user, db)
    feed_res = await db.execute(
        select(func.sum(Log.amount_kg)).join(Device, Log.device_id == Device.id)
        .where(Device.farm_id == farm_id, Log.event_type.in_([LogEventType.MANUAL_FEED, LogEventType.SCHEDULED_FEED]))
    )
    total_feed = feed_res.scalar() or 0.0
    sampling_res = await db.execute(select(Sampling).where(Sampling.farm_id == farm_id).order_by(Sampling.sample_date.desc()).limit(1))
    last_sampling = sampling_res.scalar_one_or_none()
    
    biomass = 0.0
    fcr = 0.0
    last_date = None
    if last_sampling:
        biomass = (last_sampling.abw_gram * last_sampling.population) / 1000.0
        if biomass > 0: fcr = total_feed / biomass
        last_date = last_sampling.sample_date

    return AnalyticsOut(total_feed_kg=round(total_feed, 2), current_biomass_kg=round(biomass, 2), fcr=round(fcr, 2), last_sampling_date=last_date)

@router.get("/farms/{farm_id}/charts")
async def get_charts_data(farm_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_farm_access(farm_id, user, db)
    
    # GUNAKAN PYTHON UNTUK MENGHITUNG TANGGAL (Kompatibel dengan SQLite & PostgreSQL)
    WIB = timezone(timedelta(hours=7))
    today = datetime.now(WIB).date() 
    seven_days_ago = today - timedelta(days=6)
    
    # Ambil semua log dalam 7 hari terakhir
    trend_res = await db.execute(
        select(Log)
        .join(Device, Log.device_id == Device.id)
        .where(
            Device.farm_id == farm_id,
            Log.event_type.in_([LogEventType.MANUAL_FEED, LogEventType.SCHEDULED_FEED]),
            Log.event_at >= datetime.combine(seven_days_ago, datetime.min.time(), tzinfo=WIB)
        )
    )
    logs = trend_res.scalars().all()
    
    # Kelompokkan total pakan berdasarkan tanggal WIB
    trend_data = {}
    for log in logs:
        if log.amount_kg and log.event_at:
            local_time = log.event_at.astimezone(WIB)
            date_str = local_time.strftime("%Y-%m-%d")
            trend_data[date_str] = trend_data.get(date_str, 0) + log.amount_kg
            
    labels = []
    values = []
    for i in range(7):
        d = seven_days_ago + timedelta(days=i)
        labels.append(d.strftime("%d %b"))
        values.append(round(trend_data.get(d.strftime("%Y-%m-%d"), 0.0), 2))

    # Data Stok Bak Alat (Hopper)
    devices_res = await db.execute(select(Device).where(Device.farm_id == farm_id))
    devices = devices_res.scalars().all()
    hopper_data = []
    for d in devices:
        hopper_data.append({
            "name": d.name or d.serial,
            "current": d.hopper_stock_kg,
            "max": d.max_hopper_kg
        })

    return {
        "trend": {"labels": labels, "values": values},
        "hoppers": hopper_data
    }