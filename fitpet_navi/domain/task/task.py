from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitpet_navi.core.enums import TaskStatusEnum, TaskTypeEnum
from fitpet_navi.domain.support.base import BaseMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from fitpet_navi.domain.task.task_section import TaskSection


class Task(BaseMixin, SoftDeleteMixin):
    __tablename__ = "task"
    __table_args__ = {"comment": "태스크"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="제목")
    tags: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="태그")
    task_type: Mapped[TaskTypeEnum] = mapped_column(
        String(64),
        nullable=False,
        comment="타입 (NEW_FEATURE / FEATURE_MODIFICATION / AUTOMATION_BATCH / POLICY_CHANGE)",
    )
    status: Mapped[TaskStatusEnum] = mapped_column(
        String(64),
        nullable=False,
        comment="상태 (BACKLOG / TODO / IN PROGRESS / DONE / CANCELLED)",
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="노출순서: 0이  가장 높음")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=2, comment="우선순위: 0 ~ 4, 0이 가장 높음")
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="아카이브 여부")
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="아카이브 일시"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="버전")

    # relationship
    task_sections: Mapped[list["TaskSection"]] = relationship(
        "TaskSection",
        back_populates="task",
        order_by="TaskSection.display_order",
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"

    @classmethod
    def create(
        cls,
        title: str,
        task_type: TaskTypeEnum,
        status: TaskStatusEnum,
        tags: str | None = None,
        display_order: int = 0,
        priority: int = 2,
    ) -> "Task":
        return Task(
            title=title,
            task_type=task_type,
            status=status,
            tags=tags,
            display_order=display_order,
            priority=priority,
        )

    _UPDATABLE_FIELDS = {"title", "tags", "status", "priority"}

    def update_display_order(self, display_order: int):
        self.display_order = display_order

    # def increase_version(self):
    #     self.version += 1

    def update_fields(self, **fields) -> bool:
        any_changed = False

        for key, value in fields.items():
            if key not in self._UPDATABLE_FIELDS:
                raise ValueError(f"Field '{key}' is not updatable")

            if hasattr(self, key) and getattr(self, key) != value:
                setattr(self, key, value)
                any_changed = True

        return any_changed
