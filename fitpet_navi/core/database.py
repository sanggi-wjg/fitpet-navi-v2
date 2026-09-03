import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, declarative_base, sessionmaker

from fitpet_navi.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
_db = settings.database

engine = create_engine(
    url=_db.dsn,
    pool_size=_db.pool_size,
    max_overflow=_db.max_overflow,
    pool_timeout=_db.pool_timeout,
    pool_recycle=_db.pool_recycle,
    pool_pre_ping=_db.pool_pre_ping,
    isolation_level=_db.isolation_level,
    echo=settings.debug,
    echo_pool=settings.debug,
)
session_factory = sessionmaker(
    bind=engine,
    autocommit=_db.autocommit,
    autoflush=_db.autoflush,
    expire_on_commit=_db.expire_on_commit,
)
Base: type[DeclarativeBase] = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 의존성 주입 목적
    ⚠️ 자동으로 트랜잭션의 commit, rollback 처리
    """
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("[get_db] 데이터베이스 트랜잭션 중 예외 발생.")
        raise
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    서비스 구현 로직 사용 목적
    ⚠️ 자동으로 트랜잭션의 commit, rollback 처리

    with get_db_session() as db:
        ...
    """
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("[get_db_session] 데이터베이스 트랜잭션 중 예외 발생.")
        raise
    finally:
        db.close()
