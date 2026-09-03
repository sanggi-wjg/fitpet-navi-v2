from typing import Any


def reject_null(value: Any) -> Any:
    """
    부분 수정 (JSON Merge Patch) 요청 DTO 에서 "필드 생략"과 "명시적 null"을 구분하기 위한 validator.

    생략된 필드는 기본값(None)이 되어 exclude_unset=True 로 걸러지고 validator 도 돌지 않는다.
    명시적 null 은 validator 를 거치므로, NOT NULL 컬럼에 대응하는 필드에서는 여기서 거절한다.

    사용 예:
        reject_null_fields = field_validator("title", "status", mode="before")(reject_null)
    """
    if value is None:
        raise ValueError("null 은 허용되지 않습니다. 값을 유지하려면 필드를 생략하세요.")
    return value
