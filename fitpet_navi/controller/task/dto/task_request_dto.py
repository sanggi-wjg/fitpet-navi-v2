from pydantic import BaseModel, Field, field_validator

from fitpet_navi.controller.support.validators import reject_null
from fitpet_navi.domain.task.enums import TaskStatusEnum, TaskTypeEnum


class TaskCreateRequestDto(BaseModel):
    title: str = Field(..., description="태스크 제목")
    tags: str | None = Field(default=None, description="태스크 태그")
    task_type: TaskTypeEnum = Field(..., description="태스크 타입")
    status: TaskStatusEnum = Field(..., description="태스크 상태")
    display_order: int = Field(default=0, description="노출순서: 0이  가장 높음")
    priority: int = Field(default=2, description="우선순위: 0 ~ 4, 0이 가장 높음")


class TaskReorderRequestDto(BaseModel):
    ordered_task_ids: list[int] = Field(..., description="정렬된 태스크 ID 리스트")


class TaskUpdateRequestDto(BaseModel):
    title: str | None = Field(default=None, description="태스크 제목 (null 불가)")
    tags: str | None = Field(default=None, description="태스크 태그 (null 이면 삭제)")
    status: TaskStatusEnum | None = Field(default=None, description="태스크 상태 (null 불가)")
    priority: int | None = Field(default=None, description="우선순위: 0 ~ 4, 0이 가장 높음 (null 불가)")
    version: int = Field(..., description="태스크 버전")

    # Json merge patch를 위해 pydantic에 MISSING 이라는 SENTINEL 값이 있긴한데 실험 기능 단계라 사용 안함
    reject_null_fields = field_validator("title", "status", "priority", mode="before")(reject_null)


class TaskSectionUpdateRequestDto(BaseModel):
    body: str = Field(..., description="섹션 내용")
    version: int = Field(..., description="섹션 버전")


class TaskChatRequestDto(BaseModel):
    message: str = Field(..., description="채팅 메시지")


class TaskProposalRejectRequestDto(BaseModel):
    reason: str = Field(..., description="반려 사유")
