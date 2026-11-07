"""Create durable incident records.

Revision ID: 0001
Revises: None
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("service", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(8), nullable=False),
        sa.Column("summary", sa.String(1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="ck_incidents_severity",
        ),
        sa.CheckConstraint(
            "char_length(trim(service)) BETWEEN 1 AND 100",
            name="ck_incidents_service_length",
        ),
        sa.CheckConstraint(
            "char_length(trim(summary)) BETWEEN 1 AND 1000",
            name="ck_incidents_summary_length",
        ),
    )


def downgrade() -> None:
    # Explicit rollback only: this removes all incident data in the target database.
    op.drop_table("incidents")
