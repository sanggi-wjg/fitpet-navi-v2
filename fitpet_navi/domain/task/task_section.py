from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitpet_navi.domain.support.base import Base, SoftDeleteMixin

if TYPE_CHECKING:
    from fitpet_navi.domain.task.task import Task


_EXAMPLE_MARKER = "(예:"


class TaskSection(Base, SoftDeleteMixin):
    __tablename__ = "task_section"
    __table_args__ = {"comment": "태스크 섹션"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="섹션 이름 (정책, 예외조건, 등)")
    body: Mapped[str] = mapped_column(Text, nullable=False, comment="내용")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="노출순서: 0이 가장 높음")
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="필수 여부")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="버전")

    # relationship
    task_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("task.id"), nullable=False, comment="task FK")
    task: Mapped["Task"] = relationship("Task", back_populates="task_sections")

    def __repr__(self) -> str:
        return f"<TaskSection(id={self.id}, task_id={self.task_id}, name={self.name}, version={self.version})>"

    @classmethod
    def create(
        cls,
        task_id: int,
        name: str,
        body: str,
        display_order: int,
        is_required: bool = False,
    ) -> TaskSection:
        return TaskSection(
            task_id=task_id,
            name=name,
            body=body,
            display_order=display_order,
            is_required=is_required,
        )

    @property
    def marker_count(self) -> int:
        return self.body.count(_EXAMPLE_MARKER)

    _UPDATABLE_FIELDS = {"body"}

    def update(self, **fields) -> TaskSection:
        body_changed = "body" in fields and fields["body"] != self.body

        for key, value in fields.items():
            if key not in self._UPDATABLE_FIELDS:
                raise ValueError(f"Field '{key}' is not updatable")
            setattr(self, key, value)

        if body_changed:
            self.version += 1
        return self
