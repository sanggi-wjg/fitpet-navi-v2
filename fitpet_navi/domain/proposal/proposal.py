from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitpet_navi.domain.proposal.enums import ProposalStatusEnum, ProposalToolEnum
from fitpet_navi.domain.support.base import BaseMixin, SoftDeleteMixin
from fitpet_navi.domain.task.task import Task
from fitpet_navi.domain.task.task_section import TaskSection


class Proposal(BaseMixin, SoftDeleteMixin):
    __tablename__ = "proposal"
    __table_args__ = (
        Index("ix_proposal_001", "task_id", "status"),
        Index("ix_proposal_002", "section_id", "status"),
        {"comment": "Navi 변경 제안"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    section_version: Mapped[int] = mapped_column(Integer, nullable=False, comment="제안 시점의 섹션 버전")
    tool: Mapped[ProposalToolEnum] = mapped_column(String(64), nullable=False, comment="도구 (REPLACE_SECTION)")
    tool_input: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, comment="도구 입력 (new_content, reason)")
    status: Mapped[ProposalStatusEnum] = mapped_column(
        String(64),
        nullable=False,
        default=ProposalStatusEnum.PENDING,
        comment="상태 (PENDING / ACCEPTED / REJECTED / STALE)",
    )
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True, comment="거부 사유")

    # relationship
    task_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("task.id"), nullable=False, comment="task FK")
    task: Mapped[Task] = relationship(Task)
    section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("task_section.id"), nullable=False, comment="task_section FK"
    )
    section: Mapped[TaskSection] = relationship(TaskSection)

    def __repr__(self) -> str:
        return f"<Proposal(id={self.id}, task_id={self.task_id}, section_id={self.section_id}, status={self.status})>"

    @classmethod
    def create(
        cls,
        task_id: int,
        section_id: int,
        section_version: int,
        tool: ProposalToolEnum,
        tool_input: dict[str, Any],
    ) -> Proposal:
        return Proposal(
            task_id=task_id,
            section_id=section_id,
            section_version=section_version,
            tool=tool,
            tool_input=tool_input,
            status=ProposalStatusEnum.PENDING,
        )

    @property
    def is_pending(self) -> bool:
        return self.status == ProposalStatusEnum.PENDING

    def accept(self) -> None:
        self._transition(ProposalStatusEnum.ACCEPTED)

    def reject(self, reason: str) -> None:
        self._transition(ProposalStatusEnum.REJECTED)
        self.reject_reason = reason

    def mark_stale(self) -> None:
        self._transition(ProposalStatusEnum.STALE)

    def _transition(self, to: ProposalStatusEnum) -> None:
        # 상태 전이는 PENDING 에서만 가능하다. 이미 처리된 제안은 다시 바꿀 수 없다.
        if not self.is_pending:
            raise ValueError(f"PENDING 상태의 제안만 {to} 로 바꿀 수 있습니다 (현재: {self.status})")
        self.status = to
