from functools import lru_cache

import httpx
from ollama import Client, ResponseError

from fitpet_navi.core.config import get_settings
from fitpet_navi.core.exceptions import LlmUnavailableException

settings = get_settings()


class NaviAgent:
    def __init__(self) -> None:
        self._property = settings.ollama
        self._client = Client(
            host=self._property.host,
            headers=self._property.headers,
            timeout=self._property.timeout_seconds,
        )

    def chat(self, messages: list[dict[str, str]]) -> str:
        try:
            response = self._client.chat(
                model=self._property.model,
                messages=messages,
                think=self._property.think,
                stream=False,
                options={"temperature": 0.0},
            )
        except (ResponseError, httpx.HTTPError, OSError, ValueError) as e:
            raise LlmUnavailableException("Navi 서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.") from e

        return response.message.content or "" if response.message else ""


@lru_cache
def get_navi_agent() -> NaviAgent:
    return NaviAgent()
