class ServiceException(Exception):
    def __init__(self, message: str = "서버 오류 발생 하였습니다. "):
        self.message = message
        super().__init__(self.message)


class NotFoundException(ServiceException):
    """해당하는 리소스를 찾을 수 없습니다."""


class ClientError(Exception):
    """클라이언트 공통 예외"""
