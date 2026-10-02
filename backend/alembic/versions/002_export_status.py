"""assignment export status

Revision ID: 002
Revises: 001
Create Date: 2026-10-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "assignments",
        sa.Column("export_status", sa.String(32), nullable=False, server_default="pending"),
    )
    op.add_column(
        "assignments",
        sa.Column("export_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_assignments_export_status", "assignments", ["export_status"])


def downgrade() -> None:
    op.drop_index("ix_assignments_export_status", table_name="assignments")
    op.drop_column("assignments", "export_attempts")
    op.drop_column("assignments", "export_status")
