from enum import StrEnum


class TaskStatusEnum(StrEnum):
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELED = "CANCELED"


class TaskTypeEnum(StrEnum):
    NEW_FEATURE = "NEW_FEATURE"
    FEATURE_MODIFICATION = "FEATURE_MODIFICATION"
    AUTOMATION_BATCH = "AUTOMATION_BATCH"
    POLICY_CHANGE = "POLICY_CHANGE"


TASK_TYPE_LABEL: dict[TaskTypeEnum, str] = {
    TaskTypeEnum.NEW_FEATURE: "신규 기능",
    TaskTypeEnum.FEATURE_MODIFICATION: "기존 기능 수정",
    TaskTypeEnum.AUTOMATION_BATCH: "자동화·배치",
    TaskTypeEnum.POLICY_CHANGE: "정책 변경",
}
