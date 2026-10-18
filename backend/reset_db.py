import asyncio
from app.core.database import engine
from app.models import Base
import seed

async def reset():
    print("⚠️ Menghapus semua data di database online...")
    async with engine.begin() as conn:
        # Menghapus semua tabel
        await conn.run_sync(Base.metadata.drop_all)
        # Membuat tabel baru yang kosong
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database berhasil dikosongkan.")
    
    print("🌱 Menjalankan seed ulang...")
    await seed.main()
    print("✅ Reset Selesai!")

if __name__ == "__main__":
    asyncio.run(reset())