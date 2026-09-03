from sqlalchemy import CursorResult, select, update
from sqlalchemy.orm import Session, selectinload

from fitpet_navi.domain.task.task import Task
from fitpet_navi.domain.task.task_section import TaskSection


class TaskRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, task: Task) -> Task:
        self.session.add(task)
        self.session.flush()
        return task

    def find_by_id(self, task_id: int) -> Task | None:
        stmt = select(Task).where(
            Task.id == task_id,
            Task.is_deleted.is_(False),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def find_by_id_with_related(self, task_id: int) -> Task | None:
        stmt = (
            select(Task)
            .options(
                selectinload(Task.task_sections.and_(TaskSection.is_deleted.is_(False))),
            )
            .where(
                Task.id == task_id,
                Task.is_deleted.is_(False),
            )
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def find_by_id_with_lock(self, task_id: int) -> Task | None:
        stmt = (
            select(Task)
            .where(
                Task.id == task_id,
                Task.is_deleted.is_(False),
            )
            .with_for_update()
        )

        return self.session.execute(stmt).scalar_one_or_none()

    def find_all(self) -> list[Task]:
        stmt = (
            select(Task)
            .where(
                Task.is_deleted.is_(False),
            )
            .order_by(
                Task.display_order.asc(),
                Task.id.desc(),
            )
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def find_all_by_ids(self, task_ids: list[int]) -> list[Task]:
        stmt = (
            select(Task)
            .where(
                Task.id.in_(task_ids),
                Task.is_deleted.is_(False),
            )
            .order_by(
                Task.id.desc(),
            )
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def increase_version(self, task_id: int, request_version: int) -> bool:
        stmt = (
            update(Task)
            .where(
                Task.id == task_id,
                Task.is_deleted.is_(False),
                Task.version == request_version,
            )
            .values(
                version=Task.version + 1,
            )
        )
        result = self.session.execute(stmt)
        assert isinstance(result, CursorResult)
        return result.rowcount == 1
