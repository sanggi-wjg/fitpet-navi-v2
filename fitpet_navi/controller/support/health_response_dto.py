from pydantic import BaseModel


class HealthResponseDto(BaseModel):
    status: str
