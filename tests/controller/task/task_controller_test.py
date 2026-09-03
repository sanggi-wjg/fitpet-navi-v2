from typing import Callable

from fastapi.testclient import TestClient

from fitpet_navi.core.enums import TaskTypeEnum
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
