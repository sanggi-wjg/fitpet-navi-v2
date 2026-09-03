from alembic import op

revision = "002"
down_revision = "001"


def upgrade():
    op.execute(
        """
        CREATE TABLE `proposal`
        (
            id              BIGINT      NOT NULL AUTO_INCREMENT PRIMARY KEY,
            task_id         BIGINT      NOT NULL COMMENT 'task FK',
            section_id      BIGINT      NOT NULL COMMENT 'task_section FK',
            section_version INT         NOT NULL COMMENT '제안 시점의 섹션 버전',
            tool            VARCHAR(64) NOT NULL COMMENT '도구 (REPLACE_SECTION)',
            tool_input           JSON        NOT NULL COMMENT '도구 입력 (new_content, reason)',
            status          VARCHAR(64) NOT NULL DEFAULT 'PENDING' COMMENT '상태 (PENDING / ACCEPTED / REJECTED / STALE)',
            reject_reason   TEXT        NULL COMMENT '거부 사유',

            created_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성일시',
            updated_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정일시',
            is_deleted      BOOLEAN     NOT NULL DEFAULT FALSE COMMENT '삭제여부',
            deleted_at      DATETIME(6) NOT NULL DEFAULT '9999-12-31 14:59:59.000000' COMMENT '삭제일시',

            INDEX `ix_proposal_001` (task_id, status),
            INDEX `ix_proposal_002` (section_id, status),

            CONSTRAINT `fk_proposal_001` FOREIGN KEY (task_id) REFERENCES `task` (id),
            CONSTRAINT `fk_proposal_002` FOREIGN KEY (section_id) REFERENCES `task_section` (id)

        ) ENGINE = InnoDB
          DEFAULT CHARSET = utf8mb4
          COLLATE = utf8mb4_0900_ai_ci COMMENT = '에이전트 변경 제안';
        """.strip()
    )


def downgrade():
    op.execute("DROP TABLE `proposal`;")
