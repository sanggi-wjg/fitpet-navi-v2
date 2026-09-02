from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

from fitpet_navi.core.enums import TaskStatusEnum, TaskTypeEnum

if TYPE_CHECKING:
    from fitpet_navi.domain.task.task import Task


class TaskTypeTemplate(BaseModel):
    task_type: TaskTypeEnum
    template: str


class TaskResponseDto(BaseModel):
    id: int
    title: str
    tags: str | None
    task_type: TaskTypeEnum
    status: TaskStatusEnum
    display_order: int
    priority: int
    is_archived: bool
    archived_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: Task) -> TaskResponseDto:
        return cls(
            id=entity.id,
            title=entity.title,
            tags=entity.tags,
            task_type=entity.task_type,
            status=entity.status,
            display_order=entity.display_order,
            priority=entity.priority,
            is_archived=entity.is_archived,
            archived_at=entity.archived_at,
            version=entity.version,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
