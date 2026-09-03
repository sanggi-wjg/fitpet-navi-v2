from functools import lru_cache
from typing import Any

import httpx
from ollama import Client, ResponseError

from fitpet_navi.core.config import get_settings
from fitpet_navi.core.exceptions import LlmUnavailableException

settings = get_settings()


class NaviAgent:
    def __init__(self) -> None:
        self.property = settings.ollama
        self.client = Client(
            host=self.property.host,
            headers=self.property.headers,
            timeout=self.property.timeout_seconds,
        )

    def chat(self, messages: list[dict[str, str]], format: dict[str, Any] | None = None) -> str:
        """
        format 에 JSON 스키마를 주면 Ollama 가 그 구조의 JSON 만 출력하도록 강제한다 (structured output).
        구조만 보장하므로 의미 검증(섹션 존재 여부 등)은 호출 측에서 따로 한다.
        """
        try:
            response = self.client.chat(
                model=self.property.model,
                think=self.property.think,
                stream=False,
                messages=messages,
                options={"temperature": 0.0},
                format=format,
            )
        except (ResponseError, httpx.HTTPError, OSError, ValueError) as e:
            raise LlmUnavailableException() from e

        return response.message.content or "" if response.message else ""


@lru_cache
def get_navi_agent() -> NaviAgent:
    return NaviAgent()
