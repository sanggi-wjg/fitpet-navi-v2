from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from fitpet_navi.controller.task.dto.task_response_dto import TaskSectionResponseDto
from fitpet_navi.domain.proposal.enums import ProposalStatusEnum, ProposalToolEnum
from fitpet_navi.service.proposal.proposal_service import AcceptResult, ProposalResult


class ProposalResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    section_id: int
    section_version: int = Field(description="제안 시점의 섹션 버전")
    tool: ProposalToolEnum
    tool_input: dict[str, Any]
    status: ProposalStatusEnum
    is_stale: bool = Field(description="PENDING 인데 제안 이후 섹션이 바뀌어 수락할 수 없음 (수락 시 409)")
    reject_reason: str | None
    created_at: datetime
    updated_at: datetime


class ProposalAcceptResponseDto(BaseModel):
    proposal: ProposalResponseDto
    section: TaskSectionResponseDto = Field(description="본문이 교체되고 버전이 오른 섹션")

    @classmethod
    def from_result(cls, result: AcceptResult) -> ProposalAcceptResponseDto:
        return cls(
            proposal=ProposalResponseDto.model_validate(result.proposal),
            section=TaskSectionResponseDto.model_validate(result.section),
        )


class ChatResponseDto(BaseModel):
    tool: ProposalToolEnum
    message: str | None = Field(default=None, description="no_change 일 때 담당자에게 되묻는 말")
    proposal: ProposalResponseDto | None = None
    diff: str | None = Field(default=None, description="현재 섹션 본문 → 제안 본문 unified diff")

    @classmethod
    def from_result(cls, result: ProposalResult) -> ChatResponseDto:
        return cls(
            tool=ProposalToolEnum(result.payload.tool),
            message=result.message,
            proposal=ProposalResponseDto.model_validate(result.proposal) if result.proposal else None,
            diff=result.diff or None,
        )
