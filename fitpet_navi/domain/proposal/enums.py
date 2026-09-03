from enum import StrEnum


class ProposalToolEnum(StrEnum):
    REPLACE_SECTION = "replace_section"
    NO_CHANGE = "no_change"


class ProposalStatusEnum(StrEnum):
    PENDING = "PENDING"  # 대기
    ACCEPTED = "ACCEPTED"  # 수락
    REJECTED = "REJECTED"  # 거부
    STALE = "STALE"  # 제안 시점 이후 섹션이 바뀌어 적용 불가
