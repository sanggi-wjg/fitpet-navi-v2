import logging

from fastapi import FastAPI, Request, status
from starlette.responses import JSONResponse

from fitpet_navi.controller.support.error_response_dto import ErrorResponseDto
from fitpet_navi.core.exceptions import ServiceException
from fitpet_navi.util.util_datetime import get_utc_now

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(Exception)
    async def handle_exception_handler(request: Request, e: Exception):
        logger.exception(e)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponseDto(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                statusText="INTERNAL_SERVER_ERROR",
                timestamp=get_utc_now().isoformat(),
            ).model_dump(),
        )

    @app.exception_handler(ServiceException)
    def handle_service_exception_handler(request: Request, e: ServiceException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponseDto(
                status=status.HTTP_400_BAD_REQUEST,
                statusText="BAD_REQUEST",
                message=e.message,
                timestamp=get_utc_now().isoformat(),
            ).model_dump(),
        )
