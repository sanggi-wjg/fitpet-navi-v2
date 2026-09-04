from enum import StrEnum


class ProposalToolEnum(StrEnum):
    REPLACE_SECTION = "replace_section"
    NO_CHANGE = "no_change"


class ProposalStatusEnum(StrEnum):
    PENDING = "PENDING"  # 대기
    ACCEPTED = "ACCEPTED"  # 수락
    REJECTED = "REJECTED"  # 거부
