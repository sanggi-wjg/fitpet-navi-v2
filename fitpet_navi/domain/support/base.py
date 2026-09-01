from datetime import datetime, timezone

from sqlalchemy import DateTime, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

_NOT_DELETED = datetime(9999, 12, 31, 14, 59, 59, tzinfo=timezone.utc)


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        comment="생성일시",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="수정일시",
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("'9999-12-31 14:59:59+00'"),
        default=_NOT_DELETED,
        nullable=False,
        comment="삭제일시 (9999-12-31 = 미삭제)",
    )
    is_deleted: Mapped[bool] = mapped_column(default=False, comment="삭제 여부")

    def delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
