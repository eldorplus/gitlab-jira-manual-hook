"""create durable webhook queue and dead-letter tables"""
from alembic import op
import sqlalchemy as sa

revision = "0001_queue_dlq"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "webhook_queue",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("dedupe_key", sa.String(255), nullable=False, unique=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.Column("locked_by", sa.String(255)),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_webhook_queue_available", "webhook_queue", ["available_at"])
    op.create_table(
        "webhook_dead_letters",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("queue_id", sa.BigInteger(), nullable=False),
        sa.Column("dedupe_key", sa.String(255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text()),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("requeued_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_webhook_dlq_failed_at", "webhook_dead_letters", ["failed_at"])


def downgrade() -> None:
    op.drop_table("webhook_dead_letters")
    op.drop_index("ix_webhook_queue_available", table_name="webhook_queue")
    op.drop_table("webhook_queue")
