from datetime import datetime

from pydantic import BaseModel, ConfigDict

from fitpet_navi.core.enums import TaskStatusEnum, TaskTypeEnum


class TaskSectionTemplateDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    body: str
    display_order: int
    is_required: bool


class TaskTypeTemplate(BaseModel):
    task_type: TaskTypeEnum
    sections: list[TaskSectionTemplateDto]


class TaskResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class TaskSectionResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    name: str
    body: str
    display_order: int
    is_required: bool
    version: int
    created_at: datetime
    updated_at: datetime


class TaskDetailResponseDto(TaskResponseDto):
    task_sections: list[TaskSectionResponseDto]
