from typing import Any, Sequence

from pydantic import BaseModel


class ErrorResponseDto(BaseModel):
    status: int
    statusText: str
    message: str | None = None
    details: Sequence[Any] | None = None
    timestamp: str
