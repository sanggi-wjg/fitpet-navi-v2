import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote_plus

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

type IsolationLevel = Literal["REPEATABLE READ", "READ COMMITTED", "READ UNCOMMITTED", "SERIALIZABLE"]
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class AWSSecretsManager:
    def __init__(self):
        self.client = boto3.client(
            "secretsmanager",
            region_name="ap-northeast-2",
            config=Config(
                retries={"max_attempts": 3, "mode": "standard"},
                read_timeout=10,
                connect_timeout=10,
            ),
        )

    def get_secret(self) -> dict[str, Any]:
        try:
            response = self.client.get_secret_value(SecretId="fitpet-navi-v2")
            secret_string = response.get("SecretString")
            if secret_string:
                return json.loads(secret_string)
            return {}
        except (ClientError, BotoCoreError, json.JSONDecodeError) as e:
            raise RuntimeError(f"😢😢😢 AWS Secrets Manager 비밀 값을 가져오는데 실패했습니다: {e}")
        except Exception as e:
            raise RuntimeError(f"🔥🔥🔥 AWS Secrets Manager 비밀 값을 가져오는데 실패했습니다: {e}")


class MySQLDatabaseProperty(BaseModel):
    host: str
    port: int
    database: str
    user: str
    password: str
    pool_size: int = 10
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800
    pool_pre_ping: bool = True
    autocommit: bool = False
    autoflush: bool = True
    expire_on_commit: bool = False
    isolation_level: IsolationLevel = "REPEATABLE READ"

    @property
    def dsn(self):
        encoded_password = quote_plus(self.password)
        return f"mysql+pymysql://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.database}"


class DirectoryProperty(BaseModel):
    base: str = str(_PROJECT_ROOT)

    @property
    def data(self):
        return os.path.join(self.base, "data")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env" if os.getenv("ENVIRONMENT", "local") == "local" else None,
        env_file_encoding="UTF-8",
        env_nested_delimiter="__",
        nested_model_default_partial_update=False,
    )

    debug: bool
    database: MySQLDatabaseProperty
    directory: DirectoryProperty = DirectoryProperty()

    def __init__(self, **kwargs):
        environment = os.getenv("ENVIRONMENT", "local")

        if environment != "local":
            aws_secrets_manager = AWSSecretsManager()
            secrets = aws_secrets_manager.get_secret()

            for key, value in secrets.items():
                os.environ[key.upper()] = str(value)

        super().__init__(**kwargs)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()  # type: ignore[call-arg]
    for path in [settings.directory.data]:
        os.makedirs(path, exist_ok=True)
    return settings
