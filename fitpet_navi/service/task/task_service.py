from sqlalchemy.orm import Session

from fitpet_navi.core.enums import TaskStatusEnum, TaskTypeEnum
from fitpet_navi.core.exceptions import NotFoundException
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
            raise NotFoundException(f"Task를 찾을수 없습니다. id: {task_id}")
        return task

    def create_task(
        self,
        title: str,
        task_type: TaskTypeEnum,
        status: TaskStatusEnum,
        content: str,
        tags: str | None,
        display_order: int,
        priority: int,
    ) -> Task:
        return self.task_repository.save(
            Task.create(
                title=title,
                content=content,
                tags=tags,
                task_type=task_type,
                status=status,
                display_order=display_order,
                priority=priority,
            )
        )

    def reorder_tasks(self, task_ids: list[int]) -> list[Task]:
        tasks = self.task_repository.find_all_by_ids(task_ids)
        task_map = {task.id: task for task in tasks}

        for order, task_id in enumerate(task_ids):
            task = task_map.get(task_id)
            if task is not None:
                task.display_order = order

        return sorted(tasks, key=lambda t: t.display_order)

    def update_task(self, task_id: int, **update_data) -> Task:
        task = self.task_repository.find_by_id_with_lock(task_id)
        if task is None:
            raise NotFoundException(f"Task를 찾을수 없습니다. id: {task_id}")
        return task.update(**update_data)
