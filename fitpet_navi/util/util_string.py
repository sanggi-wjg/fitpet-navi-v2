import re

REGEX_HEADING_PREFIX = re.compile(r"^#+[ \t]*")
# `## 제목` 만 헤딩이다. `##태그` 는 헤딩이 아니고, 들여쓴 `    ## ` 는 코드블록이므로 줄 첫 칸부터 매칭한다.
REGEX_LEVEL2_HEADING = re.compile(r"^##[ \t]")
# CommonMark 코드 펜스: 최대 3칸 들여쓰기 + 백틱 또는 물결 3개 이상
REGEX_CODE_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def normalize_section_name(value: str) -> str:
    """`## 예외 조건:` 처럼 헤딩 표기가 섞여 와도 이름만 남긴다."""
    return REGEX_HEADING_PREFIX.sub("", value.strip()).strip().rstrip(":").strip()


def has_level2_heading(text: str) -> bool:
    return bool(REGEX_LEVEL2_HEADING.match(text))


def find_level2_heading_outside_code_fence(text: str) -> str | None:
    """
    코드 펜스 바깥에 있는 첫 번째 `## ` 헤딩 줄을 돌려준다. 없으면 None.
    펜스 안의 `## ` 는 코드의 일부(예: 셸 주석)이므로 섹션 헤딩으로 취급하지 않는다.

    펜스는 CommonMark 규칙을 따른다: 여는 마커와 같은 문자로, 같거나 더 긴 길이의 마커만 펜스를 닫는다.
    (백틱 펜스 안의 `~~~` 는 코드이고, 닫히지 않은 펜스는 문서 끝까지 이어진다.)
    """
    open_fence: str | None = None
    for line in text.splitlines():
        fence_match = REGEX_CODE_FENCE.match(line)
        if open_fence is None:
            if fence_match:
                open_fence = fence_match.group(1)
            elif has_level2_heading(line):
                return line.rstrip()
        elif fence_match and _closes_fence(open_fence, fence_match.group(1), rest=line[fence_match.end() :]):
            open_fence = None
    return None


def _closes_fence(open_fence: str, marker: str, rest: str) -> bool:
    # 닫는 펜스는 여는 펜스와 같은 문자·같거나 긴 길이여야 하고, 마커 뒤에는 공백만 올 수 있다.
    return marker[0] == open_fence[0] and len(marker) >= len(open_fence) and not rest.strip()
