import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    client = "client"
    operator = "operator"
    admin = "admin"


class RequestStatus(str, enum.Enum):
    submitted = "submitted"
    in_progress = "in_progress"
    delivered = "delivered"
    accepted = "accepted"
    rejected = "rejected"


class EpisodeQuality(str, enum.Enum):
    good = "good"
    usable = "usable"
    bad = "bad"


class ExportStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="userrole", create_constraint=False))
    name: Mapped[str] = mapped_column(String(255))
    organisation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    requests: Mapped[list["DatasetRequest"]] = relationship(back_populates="client")


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    episode_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    robot_id: Mapped[str] = mapped_column(String(64), index=True)
    task_name: Mapped[str] = mapped_column(String(255), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    operator_name: Mapped[str] = mapped_column(String(255))
    quality: Mapped[EpisodeQuality] = mapped_column(
        Enum(EpisodeQuality, name="episodequality", create_constraint=False)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assignment: Mapped["Assignment | None"] = relationship(back_populates="episode", uselist=False)


class DatasetRequest(Base):
    __tablename__ = "dataset_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    task_name: Mapped[str] = mapped_column(String(255))
    episodes_requested: Mapped[int] = mapped_column(Integer)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="requeststatus", create_constraint=False),
        default=RequestStatus.submitted,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    client: Mapped["User"] = relationship(back_populates="requests")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="request", cascade="all, delete-orphan")
    status_history: Mapped[list["StatusHistory"]] = relationship(back_populates="request", cascade="all, delete-orphan")


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (UniqueConstraint("episode_id", name="uq_assignment_episode"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("dataset_requests.id"), index=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id"), index=True)
    assigned_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    export_status: Mapped[str] = mapped_column(String(32), default=ExportStatus.pending.value, index=True)
    export_attempts: Mapped[int] = mapped_column(Integer, default=0)

    request: Mapped["DatasetRequest"] = relationship(back_populates="assignments")
    episode: Mapped["Episode"] = relationship(back_populates="assignment")


class StatusHistory(Base):
    __tablename__ = "status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("dataset_requests.id"), index=True)
    from_status: Mapped[RequestStatus | None] = mapped_column(
        Enum(RequestStatus, name="requeststatus", create_constraint=False), nullable=True
    )
    to_status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="requeststatus", create_constraint=False)
    )
    changed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    request: Mapped["DatasetRequest"] = relationship(back_populates="status_history")
