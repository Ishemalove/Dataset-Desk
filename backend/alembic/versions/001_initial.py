"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-10-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

userrole = sa.Enum("client", "operator", "admin", name="userrole")
episodequality = sa.Enum("good", "usable", "bad", name="episodequality")
requeststatus = sa.Enum(
    "submitted", "in_progress", "delivered", "accepted", "rejected", name="requeststatus"
)


def upgrade() -> None:
    userrole.create(op.get_bind(), checkfirst=True)
    episodequality.create(op.get_bind(), checkfirst=True)
    requeststatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", userrole, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("organisation", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("episode_id", sa.String(64), nullable=False),
        sa.Column("robot_id", sa.String(64), nullable=False),
        sa.Column("task_name", sa.String(255), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("operator_name", sa.String(255), nullable=False),
        sa.Column("quality", episodequality, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_episodes_episode_id", "episodes", ["episode_id"], unique=True)
    op.create_index("ix_episodes_robot_id", "episodes", ["robot_id"])
    op.create_index("ix_episodes_task_name", "episodes", ["task_name"])
    op.create_index("ix_episodes_recorded_at", "episodes", ["recorded_at"])

    op.create_table(
        "dataset_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("task_name", sa.String(255), nullable=False),
        sa.Column("episodes_requested", sa.Integer(), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", requeststatus, nullable=False, server_default="submitted"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_dataset_requests_client_id", "dataset_requests", ["client_id"])
    op.create_index("ix_dataset_requests_status", "dataset_requests", ["status"])

    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("dataset_requests.id"), nullable=False),
        sa.Column("episode_id", sa.Integer(), sa.ForeignKey("episodes.id"), nullable=False),
        sa.Column("assigned_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("episode_id", name="uq_assignment_episode"),
    )
    op.create_index("ix_assignments_request_id", "assignments", ["request_id"])
    op.create_index("ix_assignments_episode_id", "assignments", ["episode_id"])

    op.create_table(
        "status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("dataset_requests.id"), nullable=False),
        sa.Column("from_status", requeststatus, nullable=True),
        sa.Column("to_status", requeststatus, nullable=False),
        sa.Column("changed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_status_history_request_id", "status_history", ["request_id"])


def downgrade() -> None:
    op.drop_table("status_history")
    op.drop_table("assignments")
    op.drop_table("dataset_requests")
    op.drop_table("episodes")
    op.drop_table("users")
    requeststatus.drop(op.get_bind(), checkfirst=True)
    episodequality.drop(op.get_bind(), checkfirst=True)
    userrole.drop(op.get_bind(), checkfirst=True)
