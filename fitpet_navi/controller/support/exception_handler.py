import logging

from fastapi import FastAPI, Request, status
from starlette.responses import JSONResponse

from fitpet_navi.controller.support.error_response_dto import ErrorResponseDto
from fitpet_navi.core.exceptions import OptimisticLockException, ServiceException
from fitpet_navi.util.util_datetime import get_utc_now

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(Exception)
    async def handle_exception_handler(request: Request, e: Exception):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.exception(e)

        return JSONResponse(
            status_code=status_code,
            content=ErrorResponseDto(
                status=status_code,
                statusText="INTERNAL_SERVER_ERROR",
                timestamp=get_utc_now().isoformat(),
            ).model_dump(),
        )

    @app.exception_handler(ServiceException)
    def handle_service_exception_handler(request: Request, e: ServiceException):
        status_code = status.HTTP_400_BAD_REQUEST

        return JSONResponse(
            status_code=status_code,
            content=ErrorResponseDto(
                status=status_code,
                statusText="BAD_REQUEST",
                message=e.message,
                timestamp=get_utc_now().isoformat(),
            ).model_dump(),
        )

    @app.exception_handler(OptimisticLockException)
    def handle_optimistic_lock_exception_handler(request: Request, e: OptimisticLockException):
        status_code = status.HTTP_409_CONFLICT
        logger.warning(e)

        return JSONResponse(
            status_code=status_code,
            content=ErrorResponseDto(
                status=status_code,
                statusText="CONFLICT",
                message=e.message,
                timestamp=get_utc_now().isoformat(),
            ).model_dump(),
        )
