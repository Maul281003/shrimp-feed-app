from fastapi import APIRouter
from app.api.v1 import auth, devices, farms, health, schedules, reports

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(farms.router, prefix="/farms", tags=["farms"])
api_router.include_router(devices.router, tags=["devices"])
api_router.include_router(schedules.router, tags=["schedules"])
api_router.include_router(reports.router, tags=["reports"])