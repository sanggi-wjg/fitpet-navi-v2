# CLAUDE.md

## 프로젝트

FastAPI + SQLAlchemy 2.0 + MySQL 기반 백엔드. Python 3.14, 패키지 매니저는 **uv** (`uv.lock`이 정본. `poetry.lock`은 잔재).

- 제품 스펙: `docs/spec.md` — 태스크 요구사항을 LLM (Navi)이 "제안 (proposal)"하고 사용자가 수락하는 루프가 핵심 설계.

## 명령어

```bash
# 로컬 MySQL (포트 6600)
docker compose -f docker/docker-compose.yaml up -d

# 마이그레이션
uv run alembic upgrade head
uv run alembic revision -m "설명"   # ⚠️ autogenerate 불가 (아래 참고)

# 서버 실행 (localhost:9000, /docs 에 OpenAPI)
uv run python main.py

# 린트 / 포맷 / 타입체크 — pre-commit이 돌리는 것과 동일
uv run ruff check --fix
uv run ruff format
uv run pyright

# 테스트 (tests/ 디렉터리, testcontainers[mysql] 사용 — Docker 필요)
uv run pytest
uv run pytest tests/controller/task/task_controller_test.py::TaskControllerTest::test_get_task
```

`.env`는 `.env.template` 복사해서 생성. 중첩 설정은 `__` 구분자 (`DATABASE__HOST`, `OLLAMA__HOST`).

## 아키텍처

### 레이어 구조

`controller → service → repository → domain` 단방향. 각 레이어는 도메인별 서브패키지로 나뉜다 (`controller/task/`, `service/task/`, …).

- **controller**: 라우터 + DTO 변환만. `Depends(get_db)`로 세션을 받아 `Service(db)`를 그 자리에서 생성한다 (DI 컨테이너 없음). 라우터에 400/404/409/500 `responses`를 `ErrorResponseDto`로 선언한다.
- **service**: 비즈니스 로직. 없는 리소스는 `NotFoundException` 계열 (`TaskNotFoundException` 등) 발생. 여러 리포지토리를 조합할 수 있다.
- **repository**: SQLAlchemy 2.0 `select()` 스타일. 생성자로 `Session`을 받는다. 모든 조회에 `is_deleted.is_(False)` 조건 필수 — 조인·`selectinload` 대상에도 동일하게 건다 (`Task.task_sections.and_(TaskSection.is_deleted.is_(False))`).
- **domain**: SQLAlchemy 엔티티. 생성은 `Entity.create(...)` 클래스메서드, 수정은 `entity.update_fields(**fields) -> bool` — `_UPDATABLE_FIELDS` 화이트리스트 밖의 필드는 `ValueError`, 실제로 값이 바뀌었는지를 반환한다.
- **agent**: `agent/navi_agent.py`의 `NaviAgent` — Ollama 클라이언트 래퍼 (`get_navi_agent()`, lru_cache). `agent/proposal/`의 `ProposalGenerator`가 시스템 프롬프트(`prompts.py`) + 문서로 LLM을 호출해 `ProposalPayload`(`models.py`, `NoChange | ReplaceSection`)를 돌려준다. 서비스는 이를 직접 만들지 않고 `chat`·`reject` 메서드 인자로 받는다 (컨트롤러가 `Depends(get_proposal_generator)`로 주입).

DTO는 `controller/<domain>/dto/` 에 `*RequestDto` / `*ResponseDto`. 응답 DTO는 `ConfigDict(from_attributes=True)` + `ResponseDto.model_validate(entity)`로 변환한다. 부분 수정 요청은 `model_dump(exclude_unset=True)`로 넘긴다.

### 태스크와 섹션

`Task` 1 : N `TaskSection`. 섹션 집합은 `domain/task/task_section_template.py`의 타입별 템플릿이 정하고 **태스크 생성 시 확정**된다 — 추가·삭제·순서 변경 API 없음. 템플릿 본문의 예제 마커(`domain/task/constants.py`의 `EXAMPLE_MARKER`) 수가 `example_marker_count`(예제 텍스트 잔존 여부 판정)다. `GET /api/v1/tasks/templates`가 템플릿을 그대로 노출한다.

### 제안 (proposal) 루프

에이전트는 문서를 직접 쓰지 않고 **제안만** 만든다. 쓰기는 사용자의 수락에서만 일어난다.

- `ProposalGenerator.generate(task, message, rejection_context)`: Ollama **structured output**(`format=PROPOSAL_JSON_SCHEMA`)으로 구조를 강제하고, pydantic validator + "문서에 있는 섹션명인지" 검사로 의미를 검증한다. 실패하면 오류를 붙여 1회 재요청, 그래도 실패면 `LlmContractViolationException`(503). 프롬프트에는 `<sections>`(이름·필수 여부·예제 마커 수)를 서버가 넣어 준다.
- `ProposalService.chat`: `NoChange`면 저장 없이 message만 응답. `ReplaceSection`이면 `Proposal.create_for_section(section, …)`으로 PENDING 저장 + 서버가 계산한 diff(`util/util_diff.py`) 응답. **task_id·section_id·section_version은 섹션 하나에서 파생**한다 — 두 FK를 따로 받는 팩토리를 두지 않는다.
- `accept`: proposal `FOR UPDATE` → PENDING 아니면 400 → `section.version != proposal.section_version`이면 `ProposalStaleException`(409) → 같으면 섹션 body 교체 + `increase_version` + ACCEPTED. **stale은 저장하지 않고 파생**한다(`Proposal.is_stale`) — 예외로 롤백되므로 저장할 수도 없다. `task.version`은 올리지 않는다(섹션 편집과 동일).
- `reject`: REJECTED + 사유 저장 후 `RejectionContext`를 담아 바로 재제안. LLM 장애면 요청 전체가 롤백되어 거부도 남지 않는다.
- `close`: PENDING → CLOSED. 화면의 "닫기"로, 섹션·LLM을 건드리지 않으며 stale이어도 닫을 수 있다. 목록에는 이력으로 남는다.
- `update_field`(제목·태그 제안)는 **제거**. 모델이 제목을 바꾸자고 하면 `no_change` message로 제안하고 담당자가 직접 고친다.
- 라우터는 `controller/proposal/proposal_controller.py` (prefix `/api/v1`, `/tasks/{id}/chat`·`/tasks/{id}/proposals`·`/proposals/{id}/accept|reject|close`). generator는 LLM을 쓰는 chat·reject 라우트만 `Depends(get_proposal_generator)`로 주입해 서비스 메서드에 넘긴다 (테스트에서 바꿔 끼운다). 조회·수락 라우트는 Ollama 클라이언트를 만들지 않는다.
- 프롬프트·전송 방식 실험은 `playground/playground_ollama.py` (gitignore 대상).

### 버전과 낙관적 잠금

`Task`·`TaskSection` 모두 `version` 컬럼을 가진다. 수정 요청 DTO는 `version`을 필수로 받고, 서비스는 다음 순서로 처리한다 (`update_task_with_version`, `update_section_with_version` 참고):

1. 엔티티 조회 → 없으면 `NotFoundException`.
2. `entity.version != request_version` → `OptimisticLockException`.
3. `update_fields(**data)` — 바뀐 게 없으면 버전을 올리지 않는다.
4. 바뀌었으면 `repository.increase_version(id, request_version)` — `WHERE version = :request_version` 조건의 **원자적 UPDATE**. `rowcount != 1`이면 `OptimisticLockException`.

새로 잠금이 필요한 엔티티도 같은 패턴을 따른다.

### 트랜잭션 경계

`fitpet_navi/core/database.py`의 `get_db()` (FastAPI 의존성)와 `get_db_session()` (컨텍스트 매니저)가 **commit/rollback을 자동 처리**한다. 서비스/리포지토리에서 `commit()`을 직접 호출하지 말 것 — 리포지토리는 `flush()`까지만 한다. 조회한 엔티티를 변경하면 요청 종료 시 자동 flush/commit된다 (`reorder_tasks`가 이 방식).

`expire_on_commit=False`이므로 commit 이후에도 엔티티 속성 접근이 가능하다. 격리 수준은 `REPEATABLE READ`.

### Soft delete / 공통 컬럼

`core/database.py`의 `Base`가 declarative base. `domain/support/base.py`의 `BaseMixin` (created_at/updated_at, `Base`를 상속) + `SoftDeleteMixin` (is_deleted, deleted_at)을 엔티티가 상속한다. 미삭제 상태는 `deleted_at = 9999-12-31 14:59:59+00` — 이 센티넬 덕분에 `UNIQUE (…, deleted_at)` 제약이 소프트 삭제와 공존한다. 물리 삭제 대신 `entity.delete()`.

시각은 항상 UTC aware. 현재 시각은 `util/util_datetime.get_utc_now()`.

### 설정

`core/config.py`의 `get_settings()` (lru_cache). `ENVIRONMENT` 환경변수가 `local`이면 `.env`를 읽고, 그 외에는 **AWS Secrets Manager**(`ap-northeast-2`, SecretId `fitpet-navi-v2`)에서 값을 가져와 환경변수로 주입한다.

설정 그룹: `database` (MySQL), `ollama` (host/model/api_key/think/timeout — 로컬 데몬 경유와 Cloud 직접 접속 두 방식은 `.env.template` 참고), `directory`.

### Alembic

`alembic/env.py`의 `target_metadata`가 `None`이고 `alembic.ini`에 DSN이 하드코딩되어 있다. **autogenerate가 동작하지 않으므로** 마이그레이션은 `op.execute()`로 raw DDL을 직접 작성한다 (`alembic/versions/001_craete_task.py` 참고 — `task`, `task_section` 모두 여기 있음). 엔티티를 바꾸면 마이그레이션도 손으로 맞춰야 한다. 테스트는 마이그레이션이 아니라 `Base.metadata.create_all`로 스키마를 만들므로, 마이그레이션 누락이 테스트로 잡히지 않는다.

### 예외 처리

`controller/support/exception_handler.py`에서 전역 등록. 응답 형태는 `ErrorResponseDto`.

| 예외                                                  | 상태 코드 |
|-------------------------------------------------------|-----------|
| `NotFoundException` 계열                              | 404       |
| `OptimisticLockException` 계열 (`ProposalStaleException` 포함) | 409 |
| `LlmException` 계열 (`LlmUnavailable`, `LlmContractViolation`) | 503 |
| 그 외 `ServiceException`                              | 400       |
| 그 외 `Exception`                                     | 500       |

새 예외는 `core/exceptions.py`의 `ServiceException`(또는 `NotFoundException`)을 상속시킨다. 새 상태 코드가 필요하면 핸들러와 라우터 `responses`를 함께 추가한다.

## 테스트

- 파일 `*_test.py`, 클래스 `*Test`, 메서드 `test_*` (pytest 설정이 이 패턴만 수집한다. `test_*.py`는 **수집되지 않는다**).
- `tests/conftest.py`: 세션 스코프 MySQL 컨테이너 (`mysql:8.0`) + `create_all`. 함수 스코프 `db_session`은 commit 없이 close되어 테스트 간 롤백된다. `task_fixture`는 기본값을 덮어쓰는 팩토리 (`task_fixture(title=..., display_order=...)`).
- `tests/controller/conftest.py`: `client` 픽스처가 `get_db`를 `db_session`으로 override한 `TestClient`. override는 요청마다 `begin_nested()`(SAVEPOINT)로 감싸서 실제 `get_db`의 "요청 단위 commit / 예외 시 rollback"을 흉내 낸다 — 503 후 롤백 같은 동작을 테스트할 수 있다.
- `fake_generator` 픽스처: `get_proposal_generator`를 `FakeProposalGenerator`로 바꿔 LLM 호출 없이 제안 흐름을 테스트한다. `client`가 이 픽스처에 의존하므로 모든 컨트롤러 테스트에 자동 적용되며, 페이로드를 설정하려면 테스트에서 직접 받으면 된다. `fake.payload = ReplaceSection(...)` 또는 `fake.error = LlmUnavailableException()`을 설정하고, `fake.calls`로 `(task_id, message, rejection_context)`를 검증한다. LLM을 실제로 호출하는 테스트는 만들지 않는다.
- **테스트 범위 정책 (간소화)**: controller → service → repository 레이어 중 **컨트롤러 (HTTP) 테스트만 작성한다**. 서비스·리포지토리·도메인 엔티티의 단위 테스트는 만들지 않는다 — 그 로직은 컨트롤러 테스트가 HTTP 경유로 검증한다. 레이어에 속하지 않는 `util` 등의 순수 함수는 별도 단위 테스트를 둔다 (`tests/util/`).
- `# given / # when / # then` 주석으로 구분.
- `pyproject.toml`의 `[tool.pytest.ini_options] env`가 더미 설정을 주입하므로 `.env` 없이도 돈다.

## 컨벤션

- 주석·에러 메시지·docstring은 한국어.
- ruff line-length 120, double quote. import 정렬 (`I`) 포함 — PyCharm ruff optimizer와 CI를 맞추기 위함.
- pyright `standard` 모드 통과 필수 (pre-commit hook).
- 새 라우터는 `main.py`에서 `app.include_router()`로 등록. API prefix는 `/api/v1/...`.
- 경로 파라미터 라우트 (`/{task_id}`)보다 고정 경로 라우트 (`/reorder`, `/templates`)를 **먼저** 선언할 것.
- Enum·상수는 도메인별로 `domain/<domain>/enums.py`, `domain/<domain>/constants.py`에 둔다 (`domain/task/enums.py`의 `StrEnum` 참고). DB에는 `String` 컬럼으로 저장한다. `core`에는 도메인을 아는 값을 두지 않는다.
