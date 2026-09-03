from sqlalchemy import CursorResult, select, update
from sqlalchemy.orm import Session

from fitpet_navi.domain.task.task_section import TaskSection


class TaskSectionRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_all(self, task_sections: list[TaskSection]) -> list[TaskSection]:
        self.session.add_all(task_sections)
        self.session.flush()
        return task_sections

    def find_by_id(self, task_section_id: int) -> TaskSection | None:
        stmt = select(TaskSection).where(
            TaskSection.id == task_section_id,
            TaskSection.is_deleted.is_(False),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def increase_version(self, task_section_id: int, request_version: int) -> bool:
        stmt = (
            update(TaskSection)
            .where(
                TaskSection.id == task_section_id,
                TaskSection.is_deleted.is_(False),
                TaskSection.version == request_version,
            )
            .values(
                version=TaskSection.version + 1,
            )
        )
        result = self.session.execute(stmt)
        assert isinstance(result, CursorResult)
        return result.rowcount == 1
