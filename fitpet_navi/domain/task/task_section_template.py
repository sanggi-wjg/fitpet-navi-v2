from dataclasses import dataclass

from fitpet_navi.core.enums import TaskTypeEnum
from fitpet_navi.domain.task.task_section import TaskSection


@dataclass(frozen=True)
class TaskSectionTemplate:
    name: str
    body: str
    display_order: int
    is_required: bool = True


_SECTION_TEMPLATES_BY_TASK_TYPE: dict[TaskTypeEnum, list[TaskSectionTemplate]] = {
    TaskTypeEnum.NEW_FEATURE: [
        TaskSectionTemplate(
            name="정책",
            display_order=0,
            body="- (예: 생일인 유저에게 적립금 5,000원 발급)",
        ),
        TaskSectionTemplate(
            name="세부사항",
            display_order=1,
            body="\n".join(
                [
                    "- (예: 마케팅 동의 유저에게 알림톡 발송)",
                    "- (예: 발급 시점 — 생일 당일 09:00)",
                    "- (예: 적립금 유효기간 — 발급일로부터 30일)",
                ]
            ),
        ),
        TaskSectionTemplate(
            name="예외 조건",
            display_order=2,
            body="\n".join(
                [
                    "- (예: 마케팅 수신 동의를 하지 않은 유저는 발급 대상에서 제외)",
                    "- (예: 생일이 2월 29일인 유저는 평년에 3월 1일로 처리)",
                    "- (예: 탈퇴·휴면 계정은 제외)",
                ]
            ),
        ),
    ],
    TaskTypeEnum.FEATURE_MODIFICATION: [
        TaskSectionTemplate(
            name="현재 동작",
            display_order=0,
            body="- (예: 주문을 취소해도 사용한 적립금이 복원되지 않는다)",
        ),
        TaskSectionTemplate(
            name="세부사항",
            display_order=1,
            body="\n".join(
                [
                    "- (예: 복원 시점 — 취소 승인 즉시)",
                    "- (예: 복원된 적립금의 유효기간 — 원래 만료일 그대로 유지)",
                    '- (예: 노출 위치 — 마이페이지 > 적립금 내역에 "주문 취소 복원"으로 표기)',
                ]
            ),
        ),
        TaskSectionTemplate(
            name="예외 조건",
            display_order=2,
            body="\n".join(
                [
                    "- (예: 부분 취소는 이번 변경 대상이 아니다 — 전체 취소만 해당)",
                    "- (예: 이미 유효기간이 지난 적립금은 복원하지 않는다)",
                ]
            ),
        ),
    ],
    TaskTypeEnum.AUTOMATION_BATCH: [
        TaskSectionTemplate(
            name="정책",
            display_order=0,
            body="- (예: 생일인 유저에게 적립금 5,000원 발급)",
        ),
        TaskSectionTemplate(
            name="배치 주기",
            display_order=1,
            body="- (예: 매일 09:00 — 실제 주기로 수정하세요)",
        ),
        TaskSectionTemplate(
            name="세부사항",
            display_order=2,
            body="\n".join(
                [
                    "- (예: 발송 채널 — 알림톡, 실패 시 LMS 대체 발송)",
                    "- (예: 1회 실행당 대상 규모 — 하루 평균 300명)",
                    "- (예: 실행 결과 리포트 — 슬랙 #navi-batch 채널에 발송 건수 게시)",
                ]
            ),
        ),
        TaskSectionTemplate(
            name="예외 조건",
            display_order=3,
            body="\n".join(
                [
                    "- (예: 마케팅 수신 동의를 하지 않은 유저에게는 알림톡을 보내지 않는다)",
                    "- (예: 이미 발급받은 유저에게 중복 발급하지 않는다)",
                    "- (예: 발송에 실패해도 다음 날 재시도하지 않는다)",
                ]
            ),
        ),
    ],
    TaskTypeEnum.POLICY_CHANGE: [
        TaskSectionTemplate(
            name="변경 전 정책",
            display_order=0,
            body="- (예: 적립금 유효기간 12개월)",
        ),
        TaskSectionTemplate(
            name="변경 후 정책",
            display_order=1,
            body="- (예: 적립금 유효기간 6개월)",
        ),
        TaskSectionTemplate(
            name="적용 대상",
            display_order=2,
            body="- (예: 2026-10-01 이후 발급된 적립금부터 적용, 기존 적립금은 유효기간 유지)",
        ),
        TaskSectionTemplate(
            name="세부사항",
            display_order=3,
            body="\n".join(
                [
                    "- (예: 시행일 — 2026-10-01 00:00)",
                    "- (예: 사전 고지 — 시행 30일 전 앱 푸시 + 공지사항 게시)",
                    "- (예: 고객센터 안내 문구 갱신 필요)",
                ]
            ),
        ),
        TaskSectionTemplate(
            name="예외 조건",
            display_order=4,
            body="\n".join(
                [
                    "- (예: 이미 만료 안내를 받은 유저는 기존 유효기간을 보장한다)",
                    "- (예: 이벤트로 지급된 적립금은 기존 정책을 그대로 따른다)",
                ]
            ),
        ),
    ],
}


def get_section_templates_by_task_type() -> dict[TaskTypeEnum, list[TaskSectionTemplate]]:
    return _SECTION_TEMPLATES_BY_TASK_TYPE


def create_task_sections_factory(task_type: TaskTypeEnum, task_id: int) -> list[TaskSection]:
    templates = _SECTION_TEMPLATES_BY_TASK_TYPE.get(task_type)
    if templates is None:
        raise ValueError(f"Unsupported task type: {task_type}")

    return [
        TaskSection.create(
            task_id=task_id,
            name=template.name,
            body=template.body,
            display_order=template.display_order,
            is_required=template.is_required,
        )
        for template in templates
    ]
