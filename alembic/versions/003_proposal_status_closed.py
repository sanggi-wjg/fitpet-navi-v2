from alembic import op

revision = "003"
down_revision = "002"


def upgrade():
    # CLOSED 상태 추가. status 는 VARCHAR(64) 에 CHECK 제약이 없어 저장에는 DDL 이 필요 없고, 컬럼 comment 만 사실과 맞춘다.
    op.execute(
        """
        ALTER TABLE `proposal`
            MODIFY status VARCHAR(64) NOT NULL DEFAULT 'PENDING' COMMENT '상태 (PENDING / ACCEPTED / REJECTED / CLOSED)';
        """.strip()
    )


def downgrade():
    op.execute(
        """
        ALTER TABLE `proposal`
            MODIFY status VARCHAR(64) NOT NULL DEFAULT 'PENDING' COMMENT '상태 (PENDING / ACCEPTED / REJECTED)';
        """.strip()
    )
