import json
from dataclasses import dataclass

from sqlalchemy.orm import Session

from fitpet_navi.agent.proposal.models import NoChange, ProposalPayload, RejectionContext
from fitpet_navi.agent.proposal.prompts import REJECT_REQUEST_MESSAGE
from fitpet_navi.agent.proposal.proposal_generator import ProposalGenerator
from fitpet_navi.core.exceptions import (
    OptimisticLockException,
    ProposalAlreadyProcessedException,
    ProposalNotFoundException,
    ProposalStaleException,
    TaskNotFoundException,
    TaskSectionNameNotFoundException,
)
from fitpet_navi.domain.proposal.enums import ProposalToolEnum
from fitpet_navi.domain.proposal.proposal import Proposal
from fitpet_navi.domain.task.task import Task
from fitpet_navi.domain.task.task_section import TaskSection
from fitpet_navi.repository.proposal_repository import ProposalRepository
from fitpet_navi.repository.task_repository import TaskRepository
from fitpet_navi.service.task.task_service import TaskService
from fitpet_navi.util.util_diff import unified_diff


@dataclass(frozen=True)
class ProposalResult:
    """chat / reject 의 결과. no_change 면 proposal 이 None 이고 diff 는 빈 문자열."""

    payload: ProposalPayload
    proposal: Proposal | None = None
    diff: str = ""

    @property
    def message(self) -> str | None:
        return self.payload.message if isinstance(self.payload, NoChange) else None


@dataclass(frozen=True)
class AcceptResult:
    proposal: Proposal
    section: TaskSection


class ProposalService:
    # generator 는 LLM 을 실제로 쓰는 chat / reject 만 메서드 인자로 받는다. 컨트롤러가 Depends(get_proposal_generator) 로
    # 주입한다 (테스트에서 가짜로 교체). 생성자에서 받으면 LLM 이 필요 없는 조회·수락 경로까지 Ollama 클라이언트를 만들게 되고,
    # 기본값을 두면 주입을 빠뜨린 경로가 조용히 실제 LLM 을 호출하므로 둘 다 피한다.
    def __init__(self, session: Session):
        self.task_repository = TaskRepository(session)
        self.task_service = TaskService(session)
        self.proposal_repository = ProposalRepository(session)

    def chat(self, task_id: int, user_message: str, generator: ProposalGenerator) -> ProposalResult:
        task = self.task_repository.find_by_id_with_sections(task_id)
        if task is None:
            raise TaskNotFoundException(task_id)

        payload = generator.generate(task, user_message)
        return self._save_proposal(task, payload)

    def get_proposals(self, task_id: int) -> list[Proposal]:
        task = self.task_repository.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundException(task_id)
        return self.proposal_repository.find_all_by_task_id(task_id)

    def accept(self, proposal_id: int) -> AcceptResult:
        # stale 은 저장하지 않는다 — 409 예외로 트랜잭션이 롤백되므로 저장할 수 없고, Proposal.is_stale 이 파생 값이다.
        proposal = self._find_pending_with_lock(proposal_id)

        # 섹션 교체는 PATCH 와 같은 낙관적 잠금 절차를 따른다. 제안 시점 버전이 request_version 역할을 한다.
        try:
            section = self.task_service.update_section_with_version(
                proposal.task_id,
                proposal.section_id,
                proposal.section_version,
                body=proposal.new_content,
            )
        except OptimisticLockException as e:
            raise ProposalStaleException(proposal_id) from e

        proposal.accept()
        return AcceptResult(proposal=proposal, section=section)

    def close(self, proposal_id: int) -> Proposal:
        # 수락·거부 없이 종결한다. 섹션을 건드리지 않으므로 stale 여부와 무관하게 닫을 수 있고 LLM 도 호출하지 않는다.
        proposal = self._find_pending_with_lock(proposal_id)
        proposal.close()
        return proposal

    def reject(self, proposal_id: int, reason: str, generator: ProposalGenerator) -> ProposalResult:
        # 거부 저장과 재제안이 한 트랜잭션이다. LLM 장애(503)면 거부도 롤백되므로 클라이언트가 재시도한다.
        proposal = self._find_pending_with_lock(proposal_id)
        proposal.reject(reason)

        task = self.task_repository.find_by_id_with_sections(proposal.task_id)
        if task is None:
            raise TaskNotFoundException(proposal.task_id)

        rejection_context = RejectionContext(
            previous_proposal_json=json.dumps({"tool": proposal.tool, **proposal.tool_input}, ensure_ascii=False),
            reason=reason,
        )
        payload = generator.generate(task, REJECT_REQUEST_MESSAGE, rejection_context)
        return self._save_proposal(task, payload)

    def _find_pending_with_lock(self, proposal_id: int) -> Proposal:
        proposal = self.proposal_repository.find_by_id_with_lock(proposal_id)
        if proposal is None:
            raise ProposalNotFoundException(proposal_id)
        if not proposal.is_pending:
            raise ProposalAlreadyProcessedException(proposal_id, proposal.status)
        return proposal

    def _save_proposal(self, task: Task, payload: ProposalPayload) -> ProposalResult:
        if isinstance(payload, NoChange):
            return ProposalResult(payload=payload)

        # generator 가 섹션명을 이미 검증했으므로 방어 코드
        section = task.find_section(payload.section)
        if section is None:
            raise TaskSectionNameNotFoundException(payload.section)

        # 현재 본문과 같은 제안은 제안이 아니다 — 저장하지 않고 이유만 no_change 로 돌려준다.
        # 문자열 비교가 아니라 diff 로 판정한다: new_content 는 validator 가 strip 하지만 section.body 는 그렇지 않아,
        # 후행 개행만 다른 경우 문자열은 다르지만 사용자에게 보여줄 diff 는 비어 있다.
        diff = unified_diff(section.body, payload.new_content, name=section.name)
        if not diff:
            return ProposalResult(payload=NoChange(tool="no_change", message=payload.reason))

        proposal = self.proposal_repository.save(
            Proposal.create_for_section(
                section,
                tool=ProposalToolEnum(payload.tool),
                tool_input=payload.model_dump(exclude={"tool"}),
            )
        )
        return ProposalResult(payload=payload, proposal=proposal, diff=diff)
