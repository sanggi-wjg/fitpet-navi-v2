from typing import Callable

from fastapi.testclient import TestClient

from fitpet_navi.domain.task.enums import TaskTypeEnum
from fitpet_navi.domain.task.task import Task
from fitpet_navi.domain.task.task_section_template import get_section_templates_by_task_type


class TaskControllerTest:
    def test_get_tasks(self, client: TestClient, task_fixture: Callable[..., Task]):
        # given
        task_fixture(title="태스크 픽스쳐 1")
        task_fixture(title="태스크 픽스쳐 2")

        # when
        response = client.get("/api/v1/tasks")

        # then
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_task(self, client: TestClient, task_fixture: Callable[..., Task]):
        # given
        task = task_fixture(title="태스크 픽스쳐 1")

        # when
        response = client.get(f"/api/v1/tasks/{task.id}")

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == task.id
        assert body["title"] == task.title
        assert body["version"] == 0

    def test_create_task(self, client: TestClient):
        # given
        task_type = TaskTypeEnum.POLICY_CHANGE
        templates = get_section_templates_by_task_type()[task_type]

        # when
        response = client.post(
            "/api/v1/tasks",
            json={
                "title": "정책 변경 태스크",
                "task_type": task_type.value,
                "status": "BACKLOG",
                "tags": "정책,적립금",
                "priority": 1,
            },
        )

        # then
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "정책 변경 태스크"
        assert body["task_type"] == task_type.value
        assert body["version"] == 0

        sections = body["task_sections"]
        assert [s["name"] for s in sections] == [t.name for t in templates]
        assert [s["display_order"] for s in sections] == [t.display_order for t in templates]
        assert all(s["task_id"] == body["id"] for s in sections)
        assert all(s["version"] == 0 for s in sections)

    def test_reorder_tasks(self, client: TestClient, task_fixture: Callable[..., Task]):
        # given
        first = task_fixture(title="첫 번째", display_order=0)
        second = task_fixture(title="두 번째", display_order=1)
        third = task_fixture(title="세 번째", display_order=2)

        # when
        response = client.patch("/api/v1/tasks/reorder", json={"ordered_task_ids": [third.id, first.id, second.id]})

        # then
        assert response.status_code == 200
        body = response.json()
        assert [t["id"] for t in body] == [third.id, first.id, second.id]
        assert [t["display_order"] for t in body] == [0, 1, 2]

    def test_update_task(self, client: TestClient, task_fixture: Callable[..., Task]):
        # given
        task = task_fixture(title="수정 전")

        # when
        response = client.patch(f"/api/v1/tasks/{task.id}", json={"version": 0, "title": "수정 후"})

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "수정 후"
        assert body["version"] == 1

    def test_update_task_omitted_fields_are_unchanged(self, client: TestClient, task_fixture: Callable[..., Task]):
        # given
        task = task_fixture(title="수정 전", tags="유지", priority=1)

        # when
        response = client.patch(f"/api/v1/tasks/{task.id}", json={"version": 0, "title": "수정 후"})

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "수정 후"
        assert body["tags"] == "유지"
        assert body["priority"] == 1

    def test_update_task_null_tags_clears_tags(self, client: TestClient, task_fixture: Callable[..., Task]):
        # given
        task = task_fixture(tags="삭제될 태그")

        # when
        response = client.patch(f"/api/v1/tasks/{task.id}", json={"version": 0, "tags": None})

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["tags"] is None
        assert body["version"] == 1

    def test_update_task_null_on_not_nullable_field_is_rejected(
        self, client: TestClient, task_fixture: Callable[..., Task]
    ):
        # given
        task = task_fixture(title="수정 전")

        # when
        response = client.patch(f"/api/v1/tasks/{task.id}", json={"version": 0, "title": None})

        # then
        assert response.status_code == 422
        assert client.get(f"/api/v1/tasks/{task.id}").json()["title"] == "수정 전"

    def test_update_task_section_null_body_is_rejected(self, client: TestClient):
        # given
        created = client.post(
            "/api/v1/tasks", json={"title": "태스크", "task_type": "NEW_FEATURE", "status": "BACKLOG"}
        ).json()
        section = created["task_sections"][0]

        # when
        response = client.patch(
            f"/api/v1/tasks/{created['id']}/sections/{section['id']}",
            json={"version": 0, "body": None},
        )

        # then
        assert response.status_code == 422

    def test_update_task_section(self, client: TestClient):
        # given
        # 첫 번째 task가 아닌 task의 섹션을 대상으로 한다 (task_id 조건 검증)
        client.post("/api/v1/tasks", json={"title": "첫 번째", "task_type": "NEW_FEATURE", "status": "BACKLOG"})
        created = client.post(
            "/api/v1/tasks", json={"title": "두 번째", "task_type": "NEW_FEATURE", "status": "BACKLOG"}
        ).json()
        section = created["task_sections"][0]

        # when
        response = client.patch(
            f"/api/v1/tasks/{created['id']}/sections/{section['id']}",
            json={"version": 0, "body": "- 생일인 유저에게 적립금 5,000원 발급"},
        )

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == section["id"]
        assert body["task_id"] == created["id"]
        assert body["body"] == "- 생일인 유저에게 적립금 5,000원 발급"
        assert body["version"] == 1

    def test_archive_task(self, client: TestClient, task_fixture: Callable[..., Task]):
        # given
        task = task_fixture()

        # when
        response = client.patch(f"/api/v1/tasks/{task.id}/archive")

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == task.id
        assert body["is_archived"] is True
        assert body["archived_at"] is not None

    def test_unarchive_task(self, client: TestClient, task_fixture: Callable[..., Task]):
        # given
        task = task_fixture()
        client.patch(f"/api/v1/tasks/{task.id}/archive")

        # when
        response = client.patch(f"/api/v1/tasks/{task.id}/unarchive")

        # then
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == task.id
        assert body["is_archived"] is False
        assert body["archived_at"] is None

    def test_archive_task_not_found(self, client: TestClient):
        # when
        response = client.patch("/api/v1/tasks/999999/archive")

        # then
        assert response.status_code == 404
        assert response.json()["statusText"] == "NOT_FOUND"

    def test_get_task_not_found(self, client: TestClient):
        # when
        response = client.get("/api/v1/tasks/999999")

        # then
        assert response.status_code == 404
        assert response.json()["statusText"] == "NOT_FOUND"
