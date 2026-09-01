from enum import StrEnum


class TaskStatusEnum(StrEnum):
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELED = "CANCELED"


class TaskTypeEnum(StrEnum):
    NEW_FEATURE = "신규 기능"
    EXISTING_FEATURE_MODIFICATION = "기존 기능 수정"
    AUTOMATION_BATCH = "자동화·배치"
    POLICY_CHANGE = "정책 변경"
