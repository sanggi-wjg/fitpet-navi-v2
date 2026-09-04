from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fitpet_navi.agent.proposal.models import ProposalPayload, RejectionContext
from fitpet_navi.agent.proposal.proposal_generator import get_proposal_generator
from fitpet_navi.core.database import get_db
from fitpet_navi.domain.task.task import Task
from main import app


@pytest.fixture()
def client(db_session: Session, fake_generator: "FakeProposalGenerator") -> Generator[TestClient, None, None]:
    # fake_generator 에 의존해 모든 컨트롤러 테스트가 실제 LLM 클라이언트를 만들지 않게 한다.
    def override_get_db() -> Generator[Session, None, None]:
        with db_session.begin_nested():
            yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class FakeProposalGenerator:
    def __init__(self) -> None:
        self.payload: ProposalPayload | None = None
        self.error: Exception | None = None
        self.calls: list[tuple[int, str, RejectionContext | None]] = []

    def generate(
        self,
        task: Task,
        user_message: str,
        rejection_context: RejectionContext | None = None,
    ) -> ProposalPayload:
        self.calls.append((task.id, user_message, rejection_context))
        if self.error is not None:
            raise self.error
        assert self.payload is not None, "fake_generator.payload 를 먼저 설정하세요"
        return self.payload


@pytest.fixture()
def fake_generator() -> Generator[FakeProposalGenerator, None, None]:
    # client 픽스처가 이 픽스처에 의존하므로 같은 테스트 안에서는 동일 인스턴스를 공유한다.
    fake = FakeProposalGenerator()
    app.dependency_overrides[get_proposal_generator] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_proposal_generator, None)
