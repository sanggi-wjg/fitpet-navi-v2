import re

REGEX_HEADING_PREFIX = re.compile(r"^#+[ \t]*")
REGEX_LEVEL2_HEADING = re.compile(r"^##[^#]")


def normalize_section_name(value: str) -> str:
    """`## 예외 조건:` 처럼 헤딩 표기가 섞여 와도 이름만 남긴다."""
    return REGEX_HEADING_PREFIX.sub("", value.strip()).strip().rstrip(":").strip()


def has_level2_heading(text: str) -> bool:
    return bool(REGEX_LEVEL2_HEADING.match(text))
