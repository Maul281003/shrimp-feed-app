import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine, AsyncSessionLocal
from app.models import Base, Schedule, DeviceCommand

# FUNGSI SCHEDULER YANG SUDAH DIPERBAIKI
async def schedule_checker():
    print("⏰ Scheduler is running...")
    while True:
        try:
            # Gunakan Waktu Indonesia Barat
            now = datetime.now(timezone(timedelta(hours=7)))
            
            async with AsyncSessionLocal() as db:
                res = await db.execute(
                    select(Schedule).where(
                        Schedule.is_enabled == True,
                        Schedule.hour == now.hour,
                        Schedule.minute == now.minute
                    )
                )
                schedules = res.scalars().all()
                
                if schedules:
                    print(f"🔔 [SCHEDULER] Menemukan {len(schedules)} jadwal untuk jam {now.strftime('%H:%M')}")
                    for s in schedules:
                        cmd = DeviceCommand(
                            device_id=s.device_id, 
                            command_type="feed_now",
                            duration_motor=s.motor_duration_sec,
                            duration_blower=s.blower_duration_sec
                        )
                        db.add(cmd)
                    await db.commit()
                    
        except Exception as e:
            print(f"❌ Error di Scheduler: {e}")
            
        # Hitung sisa detik menuju menit berikutnya agar tidak "drift"
        now_after = datetime.now(timezone(timedelta(hours=7)))
        sleep_time = 60 - now_after.second + 0.5
        await asyncio.sleep(sleep_time)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Jalankan scheduler di background
    task = asyncio.create_task(schedule_checker())
    
    yield
    
    task.cancel()
    await engine.dispose()

app = FastAPI(title="Shrimp Feed App", version="0.1.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router, prefix="/api/v1")

candidates = [Path(__file__).resolve().parents[2] / "frontend", Path("/frontend")]
frontend_dir = next((p for p in candidates if p.exists()), None)
if frontend_dir:
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")