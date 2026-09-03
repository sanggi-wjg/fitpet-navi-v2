from functools import lru_cache

import httpx
from core.exceptions import LlmUnavailableException
from ollama import Client, ResponseError

from fitpet_navi.core.config import get_settings

settings = get_settings()


class NaviAgent:
    def __init__(self) -> None:
        self.property = settings.ollama
        self.client = Client(
            host=self.property.host,
            headers=self.property.headers,
            timeout=self.property.timeout_seconds,
        )

    def chat(self, messages: list[dict[str, str]]) -> str:
        try:
            response = self.client.chat(
                model=self.property.model,
                messages=messages,
                think=self.property.think,
                stream=False,
                options={"temperature": 0.0},
            )
        except (ResponseError, httpx.HTTPError, OSError, ValueError) as e:
            raise LlmUnavailableException() from e

        return response.message.content or "" if response.message else ""


@lru_cache
def get_navi_agent() -> NaviAgent:
    return NaviAgent()
