from fastapi import APIRouter, status

from fitpet_navi.controller.support.health_response_dto import HealthResponseDto

health_router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@health_router.get(
    "/liveness",
    status_code=status.HTTP_200_OK,
    response_model=HealthResponseDto,
)
async def liveness_check():
    return HealthResponseDto(status="UP")


@health_router.get(
    "/readiness",
    status_code=status.HTTP_200_OK,
    response_model=HealthResponseDto,
)
async def readiness_check():
    # todo add health check (db, cache, etc...)
    return HealthResponseDto(status="UP")
