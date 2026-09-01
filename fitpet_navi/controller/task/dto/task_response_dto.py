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
    content: str
    tags: str | None
    status: TaskStatusEnum
    display_order: int
    priority: int
    is_archived: bool
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: Task) -> TaskResponseDto:
        return cls(
            id=entity.id,
            title=entity.title,
            content=entity.content,
            tags=entity.tags,
            status=entity.status,
            display_order=entity.display_order,
            priority=entity.priority,
            is_archived=entity.is_archived,
            archived_at=entity.archived_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
