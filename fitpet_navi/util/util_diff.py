import difflib


def unified_diff(before: str, after: str, name: str = "") -> str:
    """
    두 텍스트의 unified diff 를 문자열로 돌려준다. 같으면 빈 문자열.

    제안(proposal)의 diff 는 LLM 이 아니라 서버가 계산한다 — 현재 섹션 본문과 제안된 본문을 비교한다.
    파일 헤더(---/+++)에는 name 을 그대로 쓴다 (예: 섹션 이름).
    """
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    # 마지막 줄에 개행이 없으면 difflib 가 "\\ No newline at end of file" 없이 이어 붙여 출력이 깨진다.
    if before_lines and not before_lines[-1].endswith("\n"):
        before_lines[-1] += "\n"
    if after_lines and not after_lines[-1].endswith("\n"):
        after_lines[-1] += "\n"

    return "".join(difflib.unified_diff(before_lines, after_lines, fromfile=name, tofile=name, lineterm="\n"))
