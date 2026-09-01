from pydantic import BaseModel

from fitpet_navi.core.enums import TaskStatusEnum


class TaskQuery(BaseModel):
    statuses: list[TaskStatusEnum] | None = None
    is_archived: bool | None = None
    query: str | None = None


class TaskIdQuery(BaseModel):
    task_id: int
