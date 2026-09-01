from alembic import op

revision = "001"
down_revision = None


def upgrade():
    op.execute(
        """
        CREATE TABLE task
        (
            id            BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
            title         VARCHAR(255) NOT NULL COMMENT '제목',
            content       TEXT         NOT NULL COMMENT '이름',
            tags          VARCHAR(255) NULL COMMENT '태그',
            task_type     VARCHAR(64)  NOT NULL COMMENT '타입 (신규 기능 / 기존 기능 수정 / 자동화·배치 / 정책 변경)',
            status        VARCHAR(64)  NOT NULL COMMENT '상태 (BACKLOG / TODO / IN PROGRESS / DONE / CANCELLED)',
            display_order INT          NOT NULL DEFAULT 0 COMMENT '표시순서: 0이  가장 높음',
            priority      INT          NOT NULL DEFAULT 2 COMMENT '우선순위: 0 ~ 4, 0이 가장 높음',
            is_archived   BOOLEAN      NOT NULL DEFAULT FALSE COMMENT '아카이브 여부',
            archived_at   DATETIME(6)  NULL,

            created_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            updated_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            is_deleted    BOOLEAN      NOT NULL DEFAULT FALSE,
            deleted_at    DATETIME(6)  NOT NULL DEFAULT '9999-12-31 14:59:59.000000'

        ) ENGINE = InnoDB
          DEFAULT CHARSET = utf8mb4
          COLLATE = utf8mb4_0900_ai_ci COMMENT = '태스크';
        """.strip()
    )


def downgrade():
    op.execute("DROP TABLE task;")
