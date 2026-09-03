from sqlalchemy import select
from sqlalchemy.orm import Session

from fitpet_navi.domain.proposal.enums import ProposalStatusEnum
from fitpet_navi.domain.proposal.proposal import Proposal


class ProposalRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, proposal: Proposal) -> Proposal:
        self.session.add(proposal)
        self.session.flush()
        return proposal

    def find_by_id(self, proposal_id: int) -> Proposal | None:
        stmt = select(Proposal).where(
            Proposal.id == proposal_id,
            Proposal.is_deleted.is_(False),
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def find_by_id_with_lock(self, proposal_id: int) -> Proposal | None:
        stmt = (
            select(Proposal)
            .where(
                Proposal.id == proposal_id,
                Proposal.is_deleted.is_(False),
            )
            .with_for_update()
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def find_all_by_task_id(self, task_id: int, status: ProposalStatusEnum | None = None) -> list[Proposal]:
        stmt = (
            select(Proposal)
            .where(
                Proposal.task_id == task_id,
                Proposal.is_deleted.is_(False),
            )
            .order_by(Proposal.id.desc())
        )
        if status is not None:
            stmt = stmt.where(Proposal.status == status)
        return list(self.session.execute(stmt).scalars().all())

    def find_all_by_section_id(self, section_id: int, status: ProposalStatusEnum | None = None) -> list[Proposal]:
        stmt = (
            select(Proposal)
            .where(
                Proposal.section_id == section_id,
                Proposal.is_deleted.is_(False),
            )
            .order_by(Proposal.id.desc())
        )
        if status is not None:
            stmt = stmt.where(Proposal.status == status)
        return list(self.session.execute(stmt).scalars().all())
