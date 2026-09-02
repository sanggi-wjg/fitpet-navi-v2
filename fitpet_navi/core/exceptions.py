class ServiceException(Exception):
    def __init__(self, message: str = "서버 오류 발생 하였습니다. "):
        self.message = message
        super().__init__(self.message)


class NotFoundException(ServiceException):
    pass


class TaskNotFoundException(NotFoundException):
    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"id가 {task_id}인 Task를 찾을 수 없습니다")


class OptimisticLockException(ServiceException):
    def __init__(self, message: str = "다른 사용자가 먼저 수정했습니다. 새로고침 후 다시 시도해 주세요."):
        super().__init__(message)


class ClientError(Exception):
    """클라이언트 공통 예외"""
