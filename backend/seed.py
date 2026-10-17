"""
Jalankan: python seed.py
Buat data demo: owner@demo.com / demo1234
"""
import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine
from app.core.security import hash_password
from app.models import Base
from app.models.device import Device, DeviceStatus
from app.models.farm import Farm
from app.models.gateway import Gateway, GatewayStatus
from app.models.user import User, UserRole


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Cek menggunakan .com
        existing = (await db.execute(
            select(User).where(User.email == "owner@demo.com")
        )).scalar_one_or_none()
        
        if existing:
            print("Seed sudah pernah dijalankan. User owner@demo.com sudah ada.")
            return

        user = User(
            email="owner@demo.com", # <-- Menggunakan .com
            hashed_password=hash_password("demo1234"),
            full_name="Owner Demo",
            role=UserRole.OWNER,
        )
        db.add(user)
        await db.flush()

        farm = Farm(owner_id=user.id, name="Tambak Demo A", location="Pantai Utara")
        db.add(farm)
        await db.flush()

        gw = Gateway(
            farm_id=farm.id, serial="GW-2026-000001",
            name="Gateway Utama", status=GatewayStatus.UNKNOWN,
        )
        db.add(gw)

        for i in range(1, 6):
            db.add(Device(
                serial=f"PKN-2026-{i:06d}",
                name=None,
                status=DeviceStatus.UNPAIRED,
            ))

        await db.commit()
        print("✅ Seed selesai.")
        print("   Login: owner@demo.com / demo1234")
        print("   Gateway serial: GW-2026-000001")
        print("   Device serial: PKN-2026-000001 .. PKN-2026-000005")


if __name__ == "__main__":
    asyncio.run(main())