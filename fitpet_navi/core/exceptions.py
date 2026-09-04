class ServiceException(Exception):
    def __init__(self, message: str = "서버 오류 발생 하였습니다. "):
        self.message = message
        super().__init__(self.message)


class NotFoundException(ServiceException):
    pass


class LlmException(ServiceException):
    pass


class TaskNotFoundException(NotFoundException):
    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"id가 {task_id}인 Task를 찾을 수 없습니다")


class TaskSectionNotFoundException(NotFoundException):
    def __init__(self, task_section_id: int):
        self.task_section_id = task_section_id
        super().__init__(f"id가 {task_section_id}인 TaskSection를 찾을 수 없습니다")


class TaskSectionNameNotFoundException(NotFoundException):
    """섹션 이름으로 찾았을 때 (LLM 제안의 section 필드)."""

    def __init__(self, section_name: str):
        self.section_name = section_name
        super().__init__(f"이름이 '{section_name}'인 섹션이 문서에 없습니다")


class OptimisticLockException(ServiceException):
    def __init__(self, message: str = "다른 사용자가 먼저 수정했습니다. 새로고침 후 다시 시도해 주세요."):
        super().__init__(message)


class ProposalNotFoundException(NotFoundException):
    def __init__(self, proposal_id: int):
        self.proposal_id = proposal_id
        super().__init__(f"id가 {proposal_id}인 Proposal을 찾을 수 없습니다")


class ProposalStaleException(OptimisticLockException):
    """제안 시점 이후 섹션이 바뀌어 적용할 수 없다. OptimisticLockException 을 상속해 409 로 응답한다."""

    def __init__(self, proposal_id: int):
        self.proposal_id = proposal_id
        super().__init__("제안 이후 섹션이 수정되어 적용할 수 없습니다. 새로고침 후 다시 제안을 받아 주세요.")


class ProposalAlreadyProcessedException(ServiceException):
    """PENDING 이 아닌 제안을 다시 수락/거부하려 했다 (400)."""

    def __init__(self, proposal_id: int, status: str):
        self.proposal_id = proposal_id
        super().__init__(f"이미 처리된 제안입니다 (id={proposal_id}, status={status})")


class ClientError(Exception):
    """클라이언트 공통 예외"""


class LlmUnavailableException(LlmException):
    def __init__(self, message: str = "LLM을 사용할 수 없습니다. 잠시 후 다시 시도해주세요."):
        super().__init__(message)


class LlmContractViolationException(LlmException):
    """재시도 후에도 LLM 응답이 출력 계약(ProposalPayload)을 만족하지 못했다."""

    def __init__(self, message: str = "Navi 의 제안을 해석하지 못했습니다. 다시 시도해주세요."):
        super().__init__(message)
