from sqlalchemy.orm import Session

from fitpet_navi.core.enums import TaskStatusEnum, TaskTypeEnum
from fitpet_navi.core.exceptions import OptimisticLockException, TaskNotFoundException
from fitpet_navi.domain.task.task import Task
from fitpet_navi.repository.task_repository import TaskRepository


class TaskService:
    def __init__(self, session: Session):
        self.task_repository = TaskRepository(session)

    def get_tasks(self) -> list[Task]:
        return self.task_repository.find_all()

    def get_task(self, task_id: int) -> Task:
        task = self.task_repository.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundException(task_id)
        return task

    def create_task(
        self,
        title: str,
        task_type: TaskTypeEnum,
        status: TaskStatusEnum,
        tags: str | None,
        display_order: int,
        priority: int,
    ) -> Task:
        new_task = self.task_repository.save(
            Task.create(
                title=title,
                tags=tags,
                task_type=task_type,
                status=status,
                display_order=display_order,
                priority=priority,
            )
        )

        return new_task

    def reorder_tasks(self, ordered_task_ids: list[int]) -> list[Task]:
        tasks = self.task_repository.find_all_by_ids(ordered_task_ids)
        task_map = {task.id: task for task in tasks}

        for new_order, task_id in enumerate(ordered_task_ids):
            task = task_map.get(task_id)
            if task is not None:
                task.update_display_order(new_order)

        return sorted(tasks, key=lambda t: t.display_order)

    def update_task_with_version(self, task_id: int, request_version: int, **update_data) -> Task:
        task = self.task_repository.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundException(task_id)

        if task.version != request_version:
            raise OptimisticLockException()

        any_changed = task.update_fields(**update_data)
        if any_changed:
            update_version_result = self.task_repository.increase_version(task_id, request_version)
            if not update_version_result:
                raise OptimisticLockException()
        return task
