import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_farm_access
from app.core.database import get_db
from app.models.farm import Farm, FarmMember
from app.models.user import User
from app.schemas.farm import FarmCreate, FarmOut

router = APIRouter()


@router.get("", response_model=list[FarmOut])
async def list_farms(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = (await db.execute(
        select(Farm).where(Farm.owner_id == user.id)
    )).scalars().all()
    member_of = (await db.execute(
        select(Farm, FarmMember.role)
        .join(FarmMember, FarmMember.farm_id == Farm.id)
        .where(FarmMember.user_id == user.id)
    )).all()

    out: list[FarmOut] = []
    for f in owned:
        out.append(FarmOut(
            id=f.id, name=f.name, location=f.location,
            latitude=f.latitude, longitude=f.longitude, role="owner",
        ))
    for f, role in member_of:
        out.append(FarmOut(
            id=f.id, name=f.name, location=f.location,
            latitude=f.latitude, longitude=f.longitude, role=role.value,
        ))
    return out


@router.post("", response_model=FarmOut, status_code=201)
async def create_farm(
    payload: FarmCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    farm = Farm(owner_id=user.id, **payload.model_dump())
    db.add(farm)
    await db.commit()
    await db.refresh(farm)
    return FarmOut(
        id=farm.id, name=farm.name, location=farm.location,
        latitude=farm.latitude, longitude=farm.longitude, role="owner",
    )


@router.get("/{farm_id}", response_model=FarmOut)
async def get_farm(
    farm_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    farm, role = await require_farm_access(farm_id, user, db)
    return FarmOut(
        id=farm.id, name=farm.name, location=farm.location,
        latitude=farm.latitude, longitude=farm.longitude, role=role,
    )