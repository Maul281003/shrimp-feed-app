import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.farm import Farm, FarmMember
from app.models.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User tidak aktif")
    return user


async def require_farm_access(
    farm_id: uuid.UUID,
    user: User,
    db: AsyncSession,
    write: bool = False,
) -> tuple[Farm, str]:
    """
    Return (farm, role). Role: 'owner' | 'technician' | 'viewer'.
    Owner hanya bisa write. Technician bisa write. Viewer read-only.
    Return 404 jika user tidak punya akses (bukan 403, sesuai dokumen).
    """
    farm = await db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm tidak ditemukan")

    if farm.owner_id == user.id:
        return farm, "owner"

    m = (await db.execute(
        select(FarmMember).where(
            FarmMember.farm_id == farm_id, FarmMember.user_id == user.id
        )
    )).scalar_one_or_none()
    if not m:
        # Sengaja 404, bukan 403, sesuai dokumen — agar tidak bocor keberadaan data
        raise HTTPException(status_code=404, detail="Farm tidak ditemukan")

    if write and m.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Akses hanya baca")

    return farm, m.role.value