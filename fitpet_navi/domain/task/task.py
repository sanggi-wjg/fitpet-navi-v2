from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from fitpet_navi.core.enums import TaskStatusEnum, TaskTypeEnum
from fitpet_navi.domain.support.base import Base, SoftDeleteMixin


class Task(Base, SoftDeleteMixin):
    __tablename__ = "task"
    __table_args__ = {"comment": "사용자 태스크"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="태스크 ID")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="태스크 제목")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="", comment="태스크 내용")
    tags: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="태그 (쉼표 구분 문자열)")
    task_type: Mapped[TaskTypeEnum] = mapped_column(
        String(64), nullable=False, comment="타입 (신규 기능 / 기존 기능 수정 / 자동화·배치 / 정책 변경)"
    )
    status: Mapped[TaskStatusEnum] = mapped_column(String(64), nullable=False, comment="태스크 상태")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="표시순서: 0이  가장 높음")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=2, comment="우선순위: 0 ~ 4, 0이 가장 높음")
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="아카이브 여부")
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="아카이브 시각"
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"

    @classmethod
    def create(
        cls,
        title: str,
        task_type: TaskTypeEnum,
        status: TaskStatusEnum,
        content: str = "",
        tags: str | None = None,
        display_order: int = 0,
        priority: int = 2,
    ) -> "Task":
        return cls(
            title=title,
            task_type=task_type,
            status=status,
            content=content,
            tags=tags,
            display_order=display_order,
            priority=priority,
        )

    _UPDATABLE_FIELDS = {"title", "content", "tags", "status", "display_order", "priority"}

    def update(self, **fields) -> "Task":
        for key, value in fields.items():
            if key not in self._UPDATABLE_FIELDS:
                raise ValueError(f"Field '{key}' is not updatable")
            setattr(self, key, value)
        return self
