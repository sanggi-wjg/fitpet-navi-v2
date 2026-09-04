from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from fitpet_navi.agent.proposal.proposal_generator import ProposalGenerator, get_proposal_generator
from fitpet_navi.controller.proposal.dto.proposal_request_dto import ChatRequestDto, ProposalRejectRequestDto
from fitpet_navi.controller.proposal.dto.proposal_response_dto import (
    ChatResponseDto,
    ProposalAcceptResponseDto,
    ProposalResponseDto,
)
from fitpet_navi.controller.support.error_response_dto import ErrorResponseDto
from fitpet_navi.core.database import get_db
from fitpet_navi.service.proposal.proposal_service import ProposalService

proposal_router = APIRouter(
    prefix="/api/v1",
    tags=["Proposal"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad Request", "model": ErrorResponseDto},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found", "model": ErrorResponseDto},
        status.HTTP_409_CONFLICT: {"description": "Conflict", "model": ErrorResponseDto},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error", "model": ErrorResponseDto},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "LLM Unavailable", "model": ErrorResponseDto},
    },
)


@proposal_router.post(
    "/tasks/{task_id}/chat",
    status_code=status.HTTP_200_OK,
    response_model=ChatResponseDto,
)
async def chat(
    task_id: int,
    request_dto: ChatRequestDto,
    db: Session = Depends(get_db),
    generator: ProposalGenerator = Depends(get_proposal_generator),
) -> ChatResponseDto:
    service = ProposalService(db, generator)
    result = service.chat(task_id, request_dto.message)
    return ChatResponseDto.from_result(result)


@proposal_router.get(
    "/tasks/{task_id}/proposals",
    status_code=status.HTTP_200_OK,
    response_model=list[ProposalResponseDto],
)
async def get_proposals(
    task_id: int,
    db: Session = Depends(get_db),
) -> list[ProposalResponseDto]:
    service = ProposalService(db)
    proposals = service.get_proposals(task_id)
    return [ProposalResponseDto.model_validate(p) for p in proposals]


@proposal_router.post(
    "/proposals/{proposal_id}/accept",
    status_code=status.HTTP_200_OK,
    response_model=ProposalAcceptResponseDto,
)
async def accept_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
) -> ProposalAcceptResponseDto:
    service = ProposalService(db)
    result = service.accept(proposal_id)
    return ProposalAcceptResponseDto.from_result(result)


@proposal_router.post(
    "/proposals/{proposal_id}/reject",
    status_code=status.HTTP_200_OK,
    response_model=ChatResponseDto,
)
async def reject_proposal(
    proposal_id: int,
    request_dto: ProposalRejectRequestDto,
    db: Session = Depends(get_db),
    generator: ProposalGenerator = Depends(get_proposal_generator),
) -> ChatResponseDto:
    service = ProposalService(db, generator)
    result = service.reject(proposal_id, request_dto.reason)
    return ChatResponseDto.from_result(result)
