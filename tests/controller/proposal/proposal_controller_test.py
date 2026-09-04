import json

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fitpet_navi.agent.proposal.models import NoChange, ReplaceSection
from fitpet_navi.core.exceptions import LlmContractViolationException, LlmUnavailableException
from fitpet_navi.domain.proposal.proposal import Proposal
from tests.controller.conftest import FakeProposalGenerator


def create_task_with_sections(client: TestClient) -> dict:
    return client.post(
        "/api/v1/tasks",
        json={"title": "생일 적립금 자동 발급", "task_type": "AUTOMATION_BATCH", "status": "BACKLOG"},
    ).json()


NEW_CONTENT = "- 마케팅 수신 동의를 하지 않은 유저는 제외\n- 탈퇴·휴면 유저는 제외"


def create_pending_proposal(client: TestClient, fake_generator: FakeProposalGenerator, task: dict) -> dict:
    """예외 조건 섹션에 대한 PENDING 제안을 하나 만들고 proposal 응답을 돌려준다."""
    fake_generator.payload = ReplaceSection(
        tool="replace_section", section="예외 조건", new_content=NEW_CONTENT, reason="탈퇴·휴면 처리 누락"
    )
    return client.post(f"/api/v1/tasks/{task['id']}/chat", json={"message": "놓친 예외가 있나요?"}).json()["proposal"]


class ProposalControllerTest:
    def test_accept_replaces_section_body_and_bumps_version(
        self, client: TestClient, fake_generator: FakeProposalGenerator
    ):
        # given
        task = create_task_with_sections(client)
        proposal = create_pending_proposal(client, fake_generator, task)

        # when
        response = client.post(f"/api/v1/proposals/{proposal['id']}/accept")

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["proposal"]["id"] == proposal["id"]
        assert body["proposal"]["status"] == "ACCEPTED"
        assert body["proposal"]["is_stale"] is False
        assert body["section"]["id"] == proposal["section_id"]
        assert body["section"]["body"] == NEW_CONTENT
        assert body["section"]["version"] == proposal["section_version"] + 1

        detail = client.get(f"/api/v1/tasks/{task['id']}").json()
        section = next(s for s in detail["task_sections"] if s["id"] == proposal["section_id"])
        assert section["body"] == NEW_CONTENT
        assert detail["version"] == 0  # 태스크 버전은 섹션 편집과 마찬가지로 올리지 않는다

    def test_accept_stale_proposal_returns_409_and_keeps_pending(
        self, client: TestClient, fake_generator: FakeProposalGenerator
    ):
        # given
        task = create_task_with_sections(client)
        proposal = create_pending_proposal(client, fake_generator, task)
        # 제안 이후 담당자가 섹션을 직접 편집 → 섹션 버전이 앞서 간다
        edit = client.patch(
            f"/api/v1/tasks/{task['id']}/sections/{proposal['section_id']}",
            json={"version": proposal["section_version"], "body": "- 담당자가 직접 고친 내용"},
        )
        assert edit.status_code == 200

        # when
        response = client.post(f"/api/v1/proposals/{proposal['id']}/accept")

        # then
        assert response.status_code == 409
        assert response.json()["statusText"] == "CONFLICT"

        listed = client.get(f"/api/v1/tasks/{task['id']}/proposals").json()
        assert listed[0]["id"] == proposal["id"]
        assert listed[0]["status"] == "PENDING"
        assert listed[0]["is_stale"] is True

        detail = client.get(f"/api/v1/tasks/{task['id']}").json()
        section = next(s for s in detail["task_sections"] if s["id"] == proposal["section_id"])
        assert section["body"] == "- 담당자가 직접 고친 내용"

    def test_accept_twice_returns_400(self, client: TestClient, fake_generator: FakeProposalGenerator):
        # given
        task = create_task_with_sections(client)
        proposal = create_pending_proposal(client, fake_generator, task)
        assert client.post(f"/api/v1/proposals/{proposal['id']}/accept").status_code == 200

        # when
        response = client.post(f"/api/v1/proposals/{proposal['id']}/accept")

        # then
        assert response.status_code == 400
        assert response.json()["statusText"] == "BAD_REQUEST"

    def test_accept_not_found(self, client: TestClient):
        # when
        response = client.post("/api/v1/proposals/999999/accept")

        # then
        assert response.status_code == 404

    # ---------- close ----------

    def test_close_marks_proposal_closed_without_touching_section(
        self, client: TestClient, fake_generator: FakeProposalGenerator
    ):
        # given
        task = create_task_with_sections(client)
        before = next(s for s in task["task_sections"] if s["name"] == "예외 조건")
        proposal = create_pending_proposal(client, fake_generator, task)

        # when
        response = client.post(f"/api/v1/proposals/{proposal['id']}/close")

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == proposal["id"]
        assert body["status"] == "CLOSED"
        assert body["is_stale"] is False
        assert body["reject_reason"] is None

        detail = client.get(f"/api/v1/tasks/{task['id']}").json()
        section = next(s for s in detail["task_sections"] if s["id"] == proposal["section_id"])
        assert section["body"] == before["body"]
        assert section["version"] == before["version"]

        listed = client.get(f"/api/v1/tasks/{task['id']}/proposals").json()
        assert [(p["id"], p["status"]) for p in listed] == [(proposal["id"], "CLOSED")]

    def test_close_twice_returns_400(self, client: TestClient, fake_generator: FakeProposalGenerator):
        # given
        task = create_task_with_sections(client)
        proposal = create_pending_proposal(client, fake_generator, task)
        assert client.post(f"/api/v1/proposals/{proposal['id']}/close").status_code == 200

        # when
        response = client.post(f"/api/v1/proposals/{proposal['id']}/close")

        # then
        assert response.status_code == 400
        assert response.json()["statusText"] == "BAD_REQUEST"

    def test_close_accepted_proposal_returns_400(self, client: TestClient, fake_generator: FakeProposalGenerator):
        # given
        task = create_task_with_sections(client)
        proposal = create_pending_proposal(client, fake_generator, task)
        assert client.post(f"/api/v1/proposals/{proposal['id']}/accept").status_code == 200

        # when
        response = client.post(f"/api/v1/proposals/{proposal['id']}/close")

        # then
        assert response.status_code == 400
        assert response.json()["statusText"] == "BAD_REQUEST"

    def test_accept_closed_proposal_returns_400(self, client: TestClient, fake_generator: FakeProposalGenerator):
        # given — 닫힌 제안은 되살릴 수 없다
        task = create_task_with_sections(client)
        proposal = create_pending_proposal(client, fake_generator, task)
        assert client.post(f"/api/v1/proposals/{proposal['id']}/close").status_code == 200

        # when
        response = client.post(f"/api/v1/proposals/{proposal['id']}/accept")

        # then
        assert response.status_code == 400
        assert response.json()["statusText"] == "BAD_REQUEST"

    def test_close_stale_proposal_succeeds(self, client: TestClient, fake_generator: FakeProposalGenerator):
        # given — 제안 이후 섹션이 바뀌어 accept 라면 409 인 상황
        task = create_task_with_sections(client)
        proposal = create_pending_proposal(client, fake_generator, task)
        patched = client.patch(
            f"/api/v1/tasks/{task['id']}/sections/{proposal['section_id']}",
            json={"body": "- 담당자가 직접 고친 본문", "version": proposal["section_version"]},
        )
        assert patched.status_code == 200
        listed = client.get(f"/api/v1/tasks/{task['id']}/proposals").json()
        assert listed[0]["is_stale"] is True

        # when
        response = client.post(f"/api/v1/proposals/{proposal['id']}/close")

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "CLOSED"
        assert body["is_stale"] is False

    def test_close_not_found(self, client: TestClient):
        # when
        response = client.post("/api/v1/proposals/999999/close")

        # then
        assert response.status_code == 404

    # ---------- reject ----------

    def test_reject_saves_reason_and_regenerates_with_context(
        self, client: TestClient, fake_generator: FakeProposalGenerator
    ):
        # given
        task = create_task_with_sections(client)
        proposal = create_pending_proposal(client, fake_generator, task)
        fake_generator.payload = ReplaceSection(
            tool="replace_section", section="예외 조건", new_content="- 재제안 내용", reason="사유 반영"
        )

        # when
        response = client.post(f"/api/v1/proposals/{proposal['id']}/reject", json={"reason": "휴면 계정은 대상이 아님"})

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["tool"] == "replace_section"
        assert body["proposal"]["id"] != proposal["id"]
        assert body["proposal"]["status"] == "PENDING"
        assert body["proposal"]["tool_input"]["new_content"] == "- 재제안 내용"
        assert "+- 재제안 내용" in body["diff"]

        # generator 에 거부 맥락이 전달됐다
        _, user_message, context = fake_generator.calls[-1]
        assert "거부" in user_message
        assert context is not None
        assert context.reason == "휴면 계정은 대상이 아님"
        previous = json.loads(context.previous_proposal_json)
        assert previous["tool"] == "replace_section"
        assert previous["new_content"] == NEW_CONTENT

        # 이전 제안은 REJECTED + 사유
        listed = client.get(f"/api/v1/tasks/{task['id']}/proposals").json()
        rejected = next(p for p in listed if p["id"] == proposal["id"])
        assert rejected["status"] == "REJECTED"
        assert rejected["reject_reason"] == "휴면 계정은 대상이 아님"

    def test_reject_with_no_change_regeneration_saves_nothing_new(
        self, client: TestClient, fake_generator: FakeProposalGenerator
    ):
        # given
        task = create_task_with_sections(client)
        proposal = create_pending_proposal(client, fake_generator, task)
        fake_generator.payload = NoChange(tool="no_change", message="그러면 현재 문서로 충분합니다.")

        # when
        response = client.post(f"/api/v1/proposals/{proposal['id']}/reject", json={"reason": "필요 없음"})

        # then
        assert response.status_code == 200
        assert response.json()["tool"] == "no_change"
        assert response.json()["proposal"] is None

        listed = client.get(f"/api/v1/tasks/{task['id']}/proposals").json()
        assert [p["status"] for p in listed] == ["REJECTED"]

    def test_reject_llm_failure_rolls_back_rejection(self, client: TestClient, fake_generator: FakeProposalGenerator):
        # given
        task = create_task_with_sections(client)
        proposal = create_pending_proposal(client, fake_generator, task)
        fake_generator.error = LlmUnavailableException()

        # when
        response = client.post(f"/api/v1/proposals/{proposal['id']}/reject", json={"reason": "사유"})

        # then
        assert response.status_code == 503
        listed = client.get(f"/api/v1/tasks/{task['id']}/proposals").json()
        assert listed[0]["status"] == "PENDING"
        assert listed[0]["reject_reason"] is None

    def test_reject_already_processed_returns_400(self, client: TestClient, fake_generator: FakeProposalGenerator):
        # given
        task = create_task_with_sections(client)
        proposal = create_pending_proposal(client, fake_generator, task)
        assert client.post(f"/api/v1/proposals/{proposal['id']}/accept").status_code == 200

        # when
        response = client.post(f"/api/v1/proposals/{proposal['id']}/reject", json={"reason": "사유"})

        # then
        assert response.status_code == 400

    def test_reject_not_found(self, client: TestClient, fake_generator: FakeProposalGenerator):
        # when
        response = client.post("/api/v1/proposals/999999/reject", json={"reason": "사유"})

        # then
        assert response.status_code == 404
        assert fake_generator.calls == []

    # ---------- chat / list ----------

    def test_chat_no_change_returns_message_without_saving(
        self, client: TestClient, fake_generator: FakeProposalGenerator, db_session: Session
    ):
        # given
        task = create_task_with_sections(client)
        fake_generator.payload = NoChange(tool="no_change", message="배치 주기의 실제 실행 시각을 알려 주세요.")

        # when
        response = client.post(f"/api/v1/tasks/{task['id']}/chat", json={"message": "문서를 다듬어 주세요."})

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["tool"] == "no_change"
        assert body["message"] == "배치 주기의 실제 실행 시각을 알려 주세요."
        assert body["proposal"] is None
        assert body["diff"] is None
        assert db_session.execute(select(func.count()).select_from(Proposal)).scalar_one() == 0
        assert fake_generator.calls == [(task["id"], "문서를 다듬어 주세요.", None)]

    def test_chat_replace_section_saves_pending_proposal_with_diff(
        self, client: TestClient, fake_generator: FakeProposalGenerator
    ):
        # given
        task = create_task_with_sections(client)
        section = next(s for s in task["task_sections"] if s["name"] == "예외 조건")
        new_content = "- 마케팅 수신 동의를 하지 않은 유저는 제외\n- 탈퇴·휴면 유저는 제외"
        fake_generator.payload = ReplaceSection(
            tool="replace_section",
            section="예외 조건",
            new_content=new_content,
            reason="탈퇴·휴면 계정 처리가 없어 개발자가 되물을 가능성이 높습니다.",
        )

        # when
        response = client.post(f"/api/v1/tasks/{task['id']}/chat", json={"message": "놓친 예외가 있나요?"})

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["tool"] == "replace_section"
        assert body["message"] is None

        proposal = body["proposal"]
        assert proposal["task_id"] == task["id"]
        assert proposal["section_id"] == section["id"]
        assert proposal["section_version"] == section["version"]
        assert proposal["status"] == "PENDING"
        assert proposal["tool"] == "replace_section"
        assert proposal["tool_input"] == {
            "section": "예외 조건",
            "new_content": new_content,
            "reason": "탈퇴·휴면 계정 처리가 없어 개발자가 되물을 가능성이 높습니다.",
        }

        diff = body["diff"]
        assert diff.startswith("--- 예외 조건\n+++ 예외 조건\n")
        assert "+- 탈퇴·휴면 유저는 제외" in diff

    def test_chat_replace_section_identical_to_current_body_is_treated_as_no_change(
        self, client: TestClient, fake_generator: FakeProposalGenerator, db_session: Session
    ):
        # given
        task = create_task_with_sections(client)
        section = next(s for s in task["task_sections"] if s["name"] == "예외 조건")
        fake_generator.payload = ReplaceSection(
            tool="replace_section", section="예외 조건", new_content=section["body"], reason="이미 충분합니다."
        )

        # when
        response = client.post(f"/api/v1/tasks/{task['id']}/chat", json={"message": "검토해 주세요."})

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["tool"] == "no_change"
        assert body["message"] == "이미 충분합니다."
        assert body["proposal"] is None
        assert db_session.execute(select(func.count()).select_from(Proposal)).scalar_one() == 0

    def test_chat_replace_section_differing_only_by_trailing_newline_is_treated_as_no_change(
        self, client: TestClient, fake_generator: FakeProposalGenerator, db_session: Session
    ):
        # given — 섹션 본문은 후행 개행을 그대로 저장하지만, 제안의 new_content 는 validator 가 strip 한다
        task = create_task_with_sections(client)
        section = next(s for s in task["task_sections"] if s["name"] == "예외 조건")
        client.patch(
            f"/api/v1/tasks/{task['id']}/sections/{section['id']}",
            json={"body": "- 탈퇴 유저는 제외\n", "version": section["version"]},
        )
        fake_generator.payload = ReplaceSection(
            tool="replace_section", section="예외 조건", new_content="- 탈퇴 유저는 제외", reason="이미 충분합니다."
        )

        # when
        response = client.post(f"/api/v1/tasks/{task['id']}/chat", json={"message": "검토해 주세요."})

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["tool"] == "no_change"
        assert body["message"] == "이미 충분합니다."
        assert body["proposal"] is None
        assert db_session.execute(select(func.count()).select_from(Proposal)).scalar_one() == 0

    def test_get_proposals_returns_newest_first(self, client: TestClient, fake_generator: FakeProposalGenerator):
        # given
        task = create_task_with_sections(client)
        other_task = create_task_with_sections(client)
        for content in ["- 첫 번째 제안", "- 두 번째 제안"]:
            fake_generator.payload = ReplaceSection(
                tool="replace_section", section="예외 조건", new_content=content, reason="r"
            )
            client.post(f"/api/v1/tasks/{task['id']}/chat", json={"message": "m"})
        client.post(f"/api/v1/tasks/{other_task['id']}/chat", json={"message": "m"})  # 다른 태스크 — 섞이면 안 됨

        # when
        response = client.get(f"/api/v1/tasks/{task['id']}/proposals")

        # then
        assert response.status_code == 200
        body = response.json()
        assert [p["tool_input"]["new_content"] for p in body] == ["- 두 번째 제안", "- 첫 번째 제안"]
        assert all(p["task_id"] == task["id"] and p["status"] == "PENDING" for p in body)

    def test_get_proposals_task_not_found(self, client: TestClient):
        # when
        response = client.get("/api/v1/tasks/999999/proposals")

        # then
        assert response.status_code == 404

    def test_chat_task_not_found(self, client: TestClient, fake_generator: FakeProposalGenerator):
        # when
        response = client.post("/api/v1/tasks/999999/chat", json={"message": "안녕"})

        # then
        assert response.status_code == 404
        assert fake_generator.calls == []

    def test_chat_empty_message_is_rejected(self, client: TestClient, fake_generator: FakeProposalGenerator):
        # given
        task = create_task_with_sections(client)

        # when
        response = client.post(f"/api/v1/tasks/{task['id']}/chat", json={"message": ""})

        # then
        assert response.status_code == 422
        assert fake_generator.calls == []

    def test_chat_llm_contract_violation_returns_503(
        self, client: TestClient, fake_generator: FakeProposalGenerator, db_session: Session
    ):
        # given
        task = create_task_with_sections(client)
        fake_generator.error = LlmContractViolationException()

        # when
        response = client.post(f"/api/v1/tasks/{task['id']}/chat", json={"message": "검토해 주세요."})

        # then
        assert response.status_code == 503
        assert response.json()["statusText"] == "SERVICE_UNAVAILABLE"
        assert db_session.execute(select(func.count()).select_from(Proposal)).scalar_one() == 0

    def test_chat_llm_unavailable_returns_503(self, client: TestClient, fake_generator: FakeProposalGenerator):
        # given
        task = create_task_with_sections(client)
        fake_generator.error = LlmUnavailableException()

        # when
        response = client.post(f"/api/v1/tasks/{task['id']}/chat", json={"message": "검토해 주세요."})

        # then
        assert response.status_code == 503
