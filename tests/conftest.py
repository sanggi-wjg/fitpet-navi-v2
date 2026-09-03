from typing import Callable, Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.community.mysql import MySqlContainer

from fitpet_navi.core.database import Base
from fitpet_navi.domain.task.enums import TaskStatusEnum, TaskTypeEnum
from fitpet_navi.domain.task.task import Task


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    with MySqlContainer(image="mysql:8.0", dialect="pymysql") as mysql:
        engine = create_engine(
            url=mysql.get_connection_url(),
            isolation_level="REPEATABLE READ",
        )
        Base.metadata.create_all(bind=engine)

        yield engine
        engine.dispose()


@pytest.fixture(scope="session")
def db_session_factory(
    test_engine: Engine,
) -> sessionmaker[Session]:
    return sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=True,
        expire_on_commit=False,
    )


@pytest.fixture()
def db_session(
    db_session_factory: sessionmaker[Session],
) -> Generator[Session, None, None]:
    session = db_session_factory()
    yield session
    session.close()


@pytest.fixture()
def task_fixture(db_session: Session) -> Callable[..., Task]:

    def create(
        title: str = "태스크 픽스쳐",
        task_type: TaskTypeEnum = TaskTypeEnum.NEW_FEATURE,
        status: TaskStatusEnum = TaskStatusEnum.BACKLOG,
        tags: str | None = None,
        display_order: int = 0,
        priority: int = 2,
    ):
        task = Task.create(
            title=title,
            task_type=task_type,
            status=status,
            tags=tags,
            display_order=display_order,
            priority=priority,
        )
        db_session.add(task)
        db_session.flush()
        return task

    return create
