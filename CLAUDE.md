# CLAUDE.md

## 프로젝트

FastAPI + SQLAlchemy 2.0 + MySQL 기반 백엔드. Python 3.14, 패키지 매니저는 **uv** (`uv.lock`이 정본. `poetry.lock`은 잔재).
제품 스펙은 `docs/spec.md` 참고 — 태스크 요구사항을 LLM이 "제안(proposal)"하고 사용자가 수락하는 루프가 핵심 설계.

## 명령어

```bash
# 로컬 MySQL (포트 6600)
docker compose -f docker/docker-compose.yaml up -d

# 마이그레이션
uv run alembic upgrade head
uv run alembic revision -m "설명"   # ⚠️ autogenerate 불가 (아래 참고)

# 서버 실행 (localhost:8000, /docs 에 OpenAPI)
uv run python main.py

# 린트 / 포맷 / 타입체크 — pre-commit이 돌리는 것과 동일
uv run ruff check --fix
uv run ruff format
uv run pyright

# 테스트 (tests/ 디렉터리, testcontainers[mysql] 사용)
uv run pytest
uv run pytest tests/path/to/test_x.py::TestClass::test_method
```

`.env`는 `.env.template` 복사해서 생성. 중첩 설정은 `__` 구분자 (`DATABASE__HOST`).

## 아키텍처

### 레이어 구조

`controller → service → repository → domain` 단방향. 각 레이어는 도메인별 서브패키지로 나뉜다 (`controller/task/`, `service/task/`, …).

- **controller**: 라우터 + DTO 변환만. `Depends(get_db)`로 세션을 받아 `Service(db)`를 그 자리에서 생성한다 (DI 컨테이너 없음).
- **service**: 비즈니스 로직. 없는 리소스는 `NotFoundException` 발생.
- **repository**: SQLAlchemy 2.0 `select()` 스타일. 생성자로 `Session`을 받는다. 모든 조회에 `is_deleted.is_(False)` 조건 필수.
- **domain**: SQLAlchemy 엔티티. 생성은 `Entity.create(...)` 클래스메서드, 수정은 `entity.update(**fields)` — `_UPDATABLE_FIELDS` 화이트리스트 밖의 필드는 `ValueError`.

DTO는 `controller/<domain>/dto/` 에 `*RequestDto` / `*ResponseDto`. 응답 DTO는 `from_entity(entity)` 클래스메서드로 변환한다.

### 트랜잭션 경계

`fitpet_navi/core/database.py`의 `get_db()` (FastAPI 의존성)와 `get_db_session()` (컨텍스트 매니저)가 **commit/rollback을 자동 처리**한다. 서비스/리포지토리에서 `commit()`을 직접 호출하지 말 것 — 리포지토리는 `flush()`까지만 한다. 조회한 엔티티를 변경하면 요청 종료 시 자동 flush/commit된다 (`update_task`가 이 방식).

`expire_on_commit=False`이므로 commit 이후에도 엔티티 속성 접근이 가능하다.

### Soft delete

`domain/support/base.py`의 `Base` (created_at/updated_at) + `SoftDeleteMixin` (is_deleted, deleted_at). 미삭제 상태는 `deleted_at = 9999-12-31 14:59:59+00`. 물리 삭제 대신 `entity.delete()`.

### 설정

`core/config.py`의 `get_settings()` (lru_cache). `ENVIRONMENT` 환경변수가 `local`이면 `.env`를 읽고, 그 외에는 **AWS Secrets Manager**(`ap-northeast-2`, SecretId `fitpet-navi-v2`)에서 값을 가져와 환경변수로 주입한다.

### Alembic

`alembic/env.py`의 `target_metadata`가 `None`이고 `alembic.ini`에 DSN이 하드코딩되어 있다. **autogenerate가 동작하지 않으므로** 마이그레이션은 `op.execute()`로 raw DDL을 직접 작성한다 (`alembic/versions/001_craete_task.py` 참고). 엔티티를 바꾸면 마이그레이션도 손으로 맞춰야 한다.

### 예외 처리

`controller/support/exception_handler.py`에서 전역 등록. `ServiceException` 계열 → 400, 그 외 → 500, 응답 형태는 `ErrorResponseDto`. 새 예외는 `core/exceptions.py`의 `ServiceException`을 상속시킨다.

## 컨벤션

- 주석·에러 메시지·docstring은 한국어.
- ruff line-length 120, double quote. import 정렬(`I`) 포함 — PyCharm ruff optimizer와 CI를 맞추기 위함.
- pyright `standard` 모드 통과 필수 (pre-commit hook).
- 새 라우터는 `main.py`에서 `app.include_router()`로 등록. API prefix는 `/api/v1/...`.
- 경로 파라미터 라우트(`/{task_id}`)보다 고정 경로 라우트(`/reorder`)를 **먼저** 선언할 것.
