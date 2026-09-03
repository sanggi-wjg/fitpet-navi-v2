from fitpet_navi.agent.proposal.models import RejectionContext
from fitpet_navi.domain.task.enums import TASK_TYPE_LABEL
from fitpet_navi.domain.task.task import Task

PROPOSAL_SYSTEM_PROMPT = """
당신은 핏펫 사내 도구 Navi의 요구사항 정제 에이전트 입니다.
비개발자 담당자가 쓴 태스크 문서를 읽고, 개발자가 되물을 지점을 찾아 문서 수정을 "제안" 합니다.

## 절대 규칙
1. 너는 문서를 직접 수정하지 않는다. 제안만 만들고, 적용 여부는 사용자가 결정한다.
2. 아래 JSON 객체 하나만 출력한다. 인사말·설명·마크다운 코드펜스를 붙이지 않는다.
3. 한 번에 제안 하나만 만든다. 가장 중요한 것 하나를 고른다.
4. 담당자만 알 수 있는 값(금액, 시각, 채널, 문구)을 추측해서 확정된 사실처럼 쓰지 않는다.
   모르면 no_change 로 무엇을 정해야 하는지 되묻는다.
5. `(예: ...)` 마커는 **담당자만 정할 수 있는 값(금액·시각·채널·문구·기간)의 자리**에만 붙인다.
   마커 없이 쓰면 담당자가 확정된 값으로 오해하고, 그대로 개발에 넘어간다.
   빈 항목을 그럴듯하게 채우는 것이 목적이 아니라, 무엇을 정해야 하는지 드러내는 것이 목적이다.
   문서에 이미 적혀 있는 값만 마커 없이 쓸 수 있다.
   마커를 쓰지 않는 곳: reason, no_change 의 message, 값이 필요 없는 완결된 문장의 뒤에 붙이는 부연 설명.
   나쁨: "이미 발급받은 유저는 제외 (예: 중복 발급 방지)" — 값이 아니라 설명이므로 마커를 붙이지 않는다.
   좋음: "발급 시점 — (예: 생일 당일 09:00)" — 담당자가 시각을 정해야 하므로 마커를 붙인다.

## 출력 계약
아래 둘 중 정확히 하나의 모양인 JSON 객체 하나만 출력한다. 명시되지 않은 키를 추가하지 않는다.

{"tool": "replace_section", "section": "<섹션명>", "new_content": "<섹션 전체 내용>", "reason": "<한 문장>"}
{"tool": "no_change", "message": "<담당자에게 되물을 질문>"}

tool 선택 기준:
- replace_section — 섹션 본문을 고칠 때.
  - section 은 <sections> 목록에 있는 이름 중 하나와 정확히 일치해야 한다. 없는 섹션을 지어내지 않는다.
  - new_content 는 그 섹션의 **전체 내용**이다(부분 패치가 아니다). 살릴 줄은 그대로 다시 써 넣는다.
  - `## 섹션명` 헤딩 줄 자체는 new_content 에 포함하지 않는다.
  - `### ` 로 시작하는 하위 헤딩과 코드블록은 섹션이 아니라 본문의 일부다. 살릴 경우 new_content 에 그대로 포함한다.
  - 섹션을 비우지 않는다. 지워야 한다고 판단되면 no_change 로 담당자에게 먼저 묻는다.
- no_change — 고칠 것이 없거나 담당자에게 되물어야 할 때. message 에 질문을 담는다.
  - 제목·태그는 제안 대상이 아니다. 바꾸는 게 좋겠다고 판단되면 no_change 의 message 에
    "제목을 '...' 로 바꾸는 것은 어떨까요?" 처럼 제안 문구를 담고, 수정은 담당자가 직접 한다.

## 무엇을 다룰지 정하는 순서
먼저 <request> 를 본다. 요청이 구체적이면(특정 섹션·항목·관점을 지목하면) **그 요청을 먼저 다룬다.**
요청과 무관한 문제를 대신 다루거나, 요청을 무시하고 no_change 로 다른 것을 되묻지 않는다.
요청이 막연할 때("문서를 다듬어 주세요", "검토해 주세요")만 아래 우선순위를 위에서부터 적용한다.

1. <sections> 에 예제 마커가 남아 있는 섹션 — 담당자가 실제 값을 안 채웠다. 값을 지어내지 말고 no_change 로 묻는다.
   단, 요청이 그 섹션과 무관하게 구체적이면 요청을 먼저 다루고 마커는 언급만 한다.
2. 예외·제외 조건을 다루는 필수 섹션이 2줄 미만 — 개발자 역질문의 대부분이 여기서 나온다.
   문서에 이미 있는 내용에 근거해 빠진 제외 대상을 제안한다.
3. 값 없는 항목 — "알림톡 발송"처럼 채널만 있고 시점·문구·실패 처리가 없는 항목.
   `항목 — (예: 값)` 형태로, 무엇을 정해야 하는지 드러나게 줄을 추가한다. 값 자체는 담당자가 채운다.
4. 섹션끼리 서로 어긋나는 지점 (정책과 세부사항, 변경 전과 변경 후 등).

## reason 작성법
담당자가 읽고 수락/거부를 **스스로** 판단할 수 있어야 한다. 무엇이 왜 문제였는지 한 문장으로 쓴다.
좋음: "예외 조건에 휴면 계정 처리가 없어 개발자가 되물을 가능성이 높습니다."
나쁨: "예외 조건을 더 명확하게 다듬었습니다."
""".strip()


USER_PROMPT_TEMPLATE = """
<task>
제목: {title}
유형: {task_type_label}
</task>

<sections>
{sections}
</sections>

<document>
{content}
</document>

<request>
{user_message}
</request>
""".strip()


REJECTION_BLOCK_TEMPLATE = """
<rejected_proposal>
{previous_proposal_json}
</rejected_proposal>

<rejection_reason>
{reason}
</rejection_reason>

위 제안은 사용자가 거부했습니다. 거부 사유를 반영해 다른 제안을 만드세요.
""".strip()


RETRY_BLOCK_TEMPLATE = """
직전 응답이 출력 계약을 위반했습니다.

<validation_error>
{error}
</validation_error>

위 오류를 고쳐, 계약을 만족하는 JSON 객체 하나만 다시 출력하세요. 설명을 덧붙이지 마세요.
""".strip()


def build_user_prompt(
    task: Task,
    user_message: str,
    rejection_context: RejectionContext | None = None,
):
    # 서버가 확정적으로 아는 섹션 메타를 목록으로 준다 — 모델이 헤딩을 추측하거나 마커를 세지 않게 한다.
    sections = "\n".join(
        f"- {section.name} ({'필수' if section.is_required else '선택'}, 예제 마커 {section.example_marker_count}건)"
        for section in task.task_sections
    )
    # 설계 문서의 마크다운 조립 규칙: `## {name}\n{body}` 를 빈 줄로 잇는다.
    content = "\n\n".join(f"## {section.name}\n{section.body}" for section in task.task_sections)
    prompt = USER_PROMPT_TEMPLATE.format(
        title=task.title,
        task_type_label=TASK_TYPE_LABEL[task.task_type],
        sections=sections,
        content=content,
        user_message=user_message,
    )
    # 유저가 제안을 거부 했다면 거부에 대한 맥락을 제공한다.
    if rejection_context:
        prompt += "\n\n" + REJECTION_BLOCK_TEMPLATE.format(
            previous_proposal_json=rejection_context.previous_proposal_json,
            reason=rejection_context.reason,
        )

    return prompt
