import logging
import logging.config
from dataclasses import dataclass


class HealthAccessLogFilter(logging.Filter):
    """헬스체크 엔드포인트의 uvicorn 접근 로그를 걸러낸다 — 주기적 헬스체크 호출이 로그를 도배하지 않도록."""

    def filter(self, record: logging.LogRecord) -> bool:
        # uvicorn.access 레코드 args: (클라이언트 주소, 메서드, 경로, HTTP 버전, 상태 코드)
        if isinstance(record.args, tuple) and len(record.args) >= 3 and isinstance(record.args[2], str):
            path = record.args[2].partition("?")[0]
            return not (path == "/health" or path.startswith("/health/"))
        return True


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    level: str = "INFO"  # 루트 로거 레벨
    uvicorn_level: str = "INFO"
    apscheduler_level: str = "WARNING"
    sqlalchemy_level: str = "WARNING"
    format: str = "%(asctime)s.%(msecs)03d [%(levelname)-8s] %(name)s | %(funcName)s:%(lineno)d — %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    logging_config = LoggingConfig()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": logging_config.format,
                    "datefmt": logging_config.date_format,
                },
            },
            "filters": {
                "health_access": {
                    "()": HealthAccessLogFilter,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": logging_config.level,
                "handlers": ["console"],
            },
            "loggers": {
                "uvicorn": {
                    "level": logging_config.uvicorn_level,
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": logging_config.uvicorn_level,
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": logging_config.uvicorn_level,
                    "handlers": ["console"],
                    "filters": ["health_access"],
                    "propagate": False,
                },
                "apscheduler": {
                    "level": logging_config.apscheduler_level,
                    "handlers": ["console"],
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "level": logging_config.sqlalchemy_level,
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
        }
    )
