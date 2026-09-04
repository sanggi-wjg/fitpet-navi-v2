import logging
from functools import lru_cache

from pydantic import ValidationError

from fitpet_navi.agent.navi_agent import NaviAgent, get_navi_agent
from fitpet_navi.agent.proposal.models import (
    PROPOSAL_ADAPTER,
    PROPOSAL_JSON_SCHEMA,
    ProposalPayload,
    RejectionContext,
    ReplaceSection,
)
from fitpet_navi.agent.proposal.prompts import PROPOSAL_SYSTEM_PROMPT, RETRY_BLOCK_TEMPLATE, build_user_prompt
from fitpet_navi.core.exceptions import LlmContractViolationException
from fitpet_navi.domain.task.task import Task

logger = logging.getLogger(__name__)


class ProposalGenerator:
    MAX_ATTEMPTS = 2

    def __init__(self, agent: NaviAgent):
        self.agent = agent

    def generate(
        self,
        task: Task,
        user_message: str,
        rejection_context: RejectionContext | None = None,
    ) -> ProposalPayload:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": PROPOSAL_SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(task, user_message, rejection_context)},
        ]
        section_names = {section.name for section in task.task_sections}
        last_error = ""

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            raw = self.agent.chat(messages, format=PROPOSAL_JSON_SCHEMA)
            logger.info(f"[proposal] attempt={attempt} raw={raw}")

            try:
                payload = PROPOSAL_ADAPTER.validate_json(raw)
                self._validate_payload(payload, section_names)
                return payload
            except (ValidationError, ValueError) as e:
                last_error = str(e)
                logger.warning(f"[proposal] attempt={attempt} 출력 계약 위반: {last_error}")
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content": RETRY_BLOCK_TEMPLATE.format(error=last_error)})

        raise LlmContractViolationException(f"Navi 의 제안을 해석하지 못했습니다: {last_error}")

    @staticmethod
    def _validate_payload(payload: ProposalPayload, section_names: set[str]) -> None:
        if isinstance(payload, ReplaceSection) and payload.section not in section_names:
            raise ValueError(
                f"section '{payload.section}' 은 문서에 없는 섹션이다. 다음 중 하나여야 한다: {sorted(section_names)}"
            )


@lru_cache
def get_proposal_generator() -> ProposalGenerator:
    return ProposalGenerator(get_navi_agent())
