from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from fitpet_navi.controller.support.error_response_dto import ErrorResponseDto
from fitpet_navi.controller.task.dto.task_request_dto import (
    TaskCreateRequestDto,
    TaskReorderRequestDto,
    TaskSectionUpdateRequestDto,
    TaskUpdateRequestDto,
)
from fitpet_navi.controller.task.dto.task_response_dto import (
    SimpleTaskResponseDto,
    TaskResponseDto,
    TaskSectionResponseDto,
    TaskSectionTemplateDto,
    TaskTypeTemplate,
)
from fitpet_navi.core.database import get_db
from fitpet_navi.domain.task.task_section_template import get_section_templates_by_task_type
from fitpet_navi.service.task.task_service import TaskService

task_router = APIRouter(
    prefix="/api/v1/tasks",
    tags=["Task"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad Request", "model": ErrorResponseDto},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found", "model": ErrorResponseDto},
        status.HTTP_409_CONFLICT: {"description": "Conflict", "model": ErrorResponseDto},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error", "model": ErrorResponseDto},
    },
)


@task_router.get(
    "/templates",
    status_code=status.HTTP_200_OK,
    response_model=list[TaskTypeTemplate],
)
async def get_templates() -> list[TaskTypeTemplate]:
    return [
        TaskTypeTemplate(
            task_type=task_type,
            sections=[TaskSectionTemplateDto.model_validate(template) for template in templates],
        )
        for task_type, templates in get_section_templates_by_task_type().items()
    ]


@task_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[TaskResponseDto],
)
async def get_tasks(
    db: Session = Depends(get_db),
) -> list[TaskResponseDto]:
    service = TaskService(db)
    tasks = service.get_tasks()
    return [TaskResponseDto.model_validate(t) for t in tasks]


@task_router.get(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    response_model=TaskResponseDto,
)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> TaskResponseDto:
    service = TaskService(db)
    task = service.get_task(task_id)
    return TaskResponseDto.model_validate(task)


@task_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskResponseDto,
)
async def create_task(
    request_dto: TaskCreateRequestDto,
    db: Session = Depends(get_db),
) -> TaskResponseDto:
    service = TaskService(db)
    task = service.create_task(
        title=request_dto.title,
        task_type=request_dto.task_type,
        status=request_dto.status,
        tags=request_dto.tags,
        display_order=request_dto.display_order,
        priority=request_dto.priority,
    )
    return TaskResponseDto.model_validate(task)


@task_router.patch(
    "/reorder",
    status_code=status.HTTP_200_OK,
    response_model=list[SimpleTaskResponseDto],
)
async def reorder_tasks(
    request_dto: TaskReorderRequestDto,
    db: Session = Depends(get_db),
) -> list[SimpleTaskResponseDto]:
    service = TaskService(db)
    tasks = service.reorder_tasks(request_dto.ordered_task_ids)
    return [SimpleTaskResponseDto.model_validate(t) for t in tasks]


@task_router.patch(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    response_model=SimpleTaskResponseDto,
)
async def update_task(
    task_id: int,
    request_dto: TaskUpdateRequestDto,
    db: Session = Depends(get_db),
) -> SimpleTaskResponseDto:
    update_data = request_dto.model_dump(exclude_unset=True)
    request_version = update_data.pop("version")

    service = TaskService(db)
    task = service.update_task_with_version(task_id, request_version, **update_data)
    return SimpleTaskResponseDto.model_validate(task)


@task_router.patch(
    "/{task_id}/archive",
    status_code=status.HTTP_200_OK,
    response_model=SimpleTaskResponseDto,
)
async def archive_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> SimpleTaskResponseDto:
    service = TaskService(db)
    task = service.archive_task(task_id)
    return SimpleTaskResponseDto.model_validate(task)


@task_router.patch(
    "/{task_id}/unarchive",
    status_code=status.HTTP_200_OK,
    response_model=SimpleTaskResponseDto,
)
async def unarchive_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> SimpleTaskResponseDto:
    service = TaskService(db)
    task = service.unarchive_task(task_id)
    return SimpleTaskResponseDto.model_validate(task)


@task_router.patch(
    "/{task_id}/sections/{section_id}",
    status_code=status.HTTP_200_OK,
    response_model=TaskSectionResponseDto,
)
async def update_task_section(
    task_id: int,
    section_id: int,
    request_dto: TaskSectionUpdateRequestDto,
    db: Session = Depends(get_db),
) -> TaskSectionResponseDto:
    update_data = request_dto.model_dump(exclude_unset=True)
    request_version = update_data.pop("version")

    service = TaskService(db)
    task_section = service.update_section_with_version(task_id, section_id, request_version, **update_data)
    return TaskSectionResponseDto.model_validate(task_section)
