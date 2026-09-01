from pydantic import BaseModel, Field

from fitpet_navi.core.enums import TaskStatusEnum, TaskTypeEnum


class TaskCreateRequestDto(BaseModel):
    title: str = Field(..., description="태스크 제목")
    task_type: TaskTypeEnum = Field(..., description="태스크 타입")
    status: TaskStatusEnum = Field(..., description="태스크 상태")
    content: str = Field(default="", description="태스크 내용")
    tags: str | None = Field(default=None, description="태스크 태그")
    display_order: int = Field(default=0, description="표시순서: 0이  가장 높음")
    priority: int = Field(default=2, description="우선순위: 0 ~ 4, 0이 가장 높음")


class TaskReorderRequestDto(BaseModel):
    task_ids: list[int] = Field(..., description="정렬된 태스크 ID 리스트")


class TaskUpdateRequestDto(BaseModel):
    title: str | None = Field(default=None, description="태스크 제목")
    content: str | None = Field(default=None, description="태스크 내용")
    tags: str | None = Field(default=None, description="태스크 태그")
    status: TaskStatusEnum | None = Field(default=None, description="태스크 상태")
    display_order: int | None = Field(default=None, description="표시순서: 0이  가장 높음")
    priority: int | None = Field(default=None, description="우선순위: 0 ~ 4, 0이 가장 높음")
