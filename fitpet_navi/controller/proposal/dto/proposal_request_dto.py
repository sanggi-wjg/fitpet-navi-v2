from pydantic import BaseModel, Field


class ChatRequestDto(BaseModel):
    message: str = Field(..., min_length=1, description="Agent 에게 보내는 요청")


class ProposalRejectRequestDto(BaseModel):
    reason: str = Field(..., min_length=1, description="거부 사유: 재제안 프롬프트에 그대로 전달된다")
