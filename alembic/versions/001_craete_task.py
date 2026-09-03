from alembic import op

revision = "001"
down_revision = None


def upgrade():
    op.execute(
        """
        CREATE TABLE `task`
        (
            id            BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
            title         VARCHAR(255) NOT NULL COMMENT '제목',
            tags          VARCHAR(255) NULL COMMENT '태그',
            task_type     VARCHAR(64)  NOT NULL COMMENT '타입 (NEW_FEATURE / FEATURE_MODIFICATION / AUTOMATION_BATCH / POLICY_CHANGE)',
            status        VARCHAR(64)  NOT NULL COMMENT '상태 (BACKLOG / TODO / IN PROGRESS / DONE / CANCELLED)',
            display_order INT          NOT NULL DEFAULT 0 COMMENT '노출순서: 0이  가장 높음',
            priority      INT          NOT NULL DEFAULT 2 COMMENT '우선순위: 0 ~ 4, 0이 가장 높음',
            is_archived   BOOLEAN      NOT NULL DEFAULT FALSE COMMENT '아카이브 여부',
            archived_at   DATETIME(6)  NULL COMMENT '아카이브 일시',
            version       INT          NOT NULL DEFAULT 0 COMMENT '버전',

            created_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성일시',
            updated_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정일시',
            is_deleted    BOOLEAN      NOT NULL DEFAULT FALSE COMMENT '삭제여부',
            deleted_at    DATETIME(6)  NOT NULL DEFAULT '9999-12-31 14:59:59.000000' COMMENT '삭제일시'

        ) ENGINE = InnoDB
          DEFAULT CHARSET = utf8mb4
          COLLATE = utf8mb4_0900_ai_ci COMMENT = '태스크';
        """.strip()
    )

    op.execute(
        """
        CREATE TABLE `task_section`
        (
            id            BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
            task_id       BIGINT       NOT NULL COMMENT 'task FK',
            name          VARCHAR(255) NOT NULL COMMENT '섹션 이름 (정책, 예외조건, 등)',
            body          TEXT         NOT NULL COMMENT '내용',
            display_order INT          NOT NULL DEFAULT 0 COMMENT '노출순서: 0이 가장 높음',
            is_required   BOOLEAN      NOT NULL DEFAULT FALSE COMMENT '필수 여부',
            version       INT          NOT NULL DEFAULT 0 COMMENT '버전',

            created_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성일시',
            updated_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정일시',
            is_deleted    BOOLEAN      NOT NULL DEFAULT FALSE COMMENT '삭제여부',
            deleted_at    DATETIME(6)  NOT NULL DEFAULT '9999-12-31 14:59:59.000000' COMMENT '삭제일시',

            UNIQUE `uk_task_section_001` (task_id, name, deleted_at),

            CONSTRAINT `fk_task_section_001` FOREIGN KEY (task_id) REFERENCES `task` (id)

        ) ENGINE = InnoDB
          DEFAULT CHARSET = utf8mb4
          COLLATE = utf8mb4_0900_ai_ci COMMENT = '태스크 섹션';
        """.strip()
    )


def downgrade():
    op.execute("DROP TABLE `task_section`;")
    op.execute("DROP TABLE `task`;")
