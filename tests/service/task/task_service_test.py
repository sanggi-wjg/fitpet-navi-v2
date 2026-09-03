from typing import Callable

import pytest
from sqlalchemy.orm import Session

from fitpet_navi.core.enums import TaskStatusEnum, TaskTypeEnum
from fitpet_navi.domain.task.task import Task
from fitpet_navi.domain.task.task_section_template import get_section_templates_by_task_type
from fitpet_navi.service.task.task_service import TaskService


class TaskServiceTest:
    @pytest.fixture()
    def task_service(self, db_session: Session) -> TaskService:
        return TaskService(db_session)

    def test_get_tasks(self, task_service: TaskService, task_fixture: Callable[..., Task]):
        # given
        first = task_fixture(title="태스크 픽스쳐 1")
        second = task_fixture(title="태스크 픽스쳐 2")

        # when
        result = task_service.get_tasks()

        # then
        assert len(result) == 2
        assert result[0].id == second.id
        assert result[1].id == first.id

    def test_get_task(self, task_service: TaskService, task_fixture: Callable[..., Task]):
        # given
        task = task_fixture(title="태스크 픽스쳐 1")

        # when
        result = task_service.get_task(task.id)

        # then
        assert result.id == task.id
        assert result.title == task.title

    def test_create_task(self, task_service: TaskService):
        # given
        task_type = TaskTypeEnum.POLICY_CHANGE
        templates = get_section_templates_by_task_type()[task_type]

        # when
        created = task_service.create_task(
            title="정책 변경 태스크",
            task_type=task_type,
            status=TaskStatusEnum.BACKLOG,
            tags="정책,적립금",
            display_order=1,
            priority=1,
        )

        # then
        assert created.id is not None
        assert created.title == "정책 변경 태스크"
        assert created.task_type == task_type
        assert created.status == TaskStatusEnum.BACKLOG
        assert created.tags == "정책,적립금"
        assert created.display_order == 1
        assert created.priority == 1
        assert created.version == 0

        result = task_service.get_task(created.id)
        assert [s.name for s in result.task_sections] == [t.name for t in templates]
        assert [s.display_order for s in result.task_sections] == [t.display_order for t in templates]
        assert all(s.task_id == created.id for s in result.task_sections)
        assert all(s.version == 0 for s in result.task_sections)

    def test_reorder_tasks(self, task_service: TaskService, task_fixture: Callable[..., Task]):
        # given
        first = task_fixture(title="첫 번째", display_order=0)
        second = task_fixture(title="두 번째", display_order=1)
        third = task_fixture(title="세 번째", display_order=2)

        # when
        result = task_service.reorder_tasks([third.id, first.id, second.id])

        # then
        assert [t.id for t in result] == [third.id, first.id, second.id]
        assert third.display_order == 0
        assert first.display_order == 1
        assert second.display_order == 2
