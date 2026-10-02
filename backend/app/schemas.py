from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import EpisodeQuality, RequestStatus, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    name: str
    organisation: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: UserRole
    name: str
    organisation: str | None = None


class UserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None
    name: str | None = None
    organisation: str | None = None


class EpisodeOut(BaseModel):
    id: int
    episode_id: str
    robot_id: str
    task_name: str
    recorded_at: datetime
    duration_seconds: int
    operator_name: str
    quality: EpisodeQuality
    assigned: bool = False
    export_status: str | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_episode(cls, episode, assigned: bool = False) -> "EpisodeOut":
        export_status = None
        assignment = getattr(episode, "assignment", None)
        if assignment is not None:
            export_status = assignment.export_status
            assigned = True
        return cls(
            id=episode.id,
            episode_id=episode.episode_id,
            robot_id=episode.robot_id,
            task_name=episode.task_name,
            recorded_at=episode.recorded_at,
            duration_seconds=episode.duration_seconds,
            operator_name=episode.operator_name,
            quality=episode.quality,
            assigned=assigned,
            export_status=export_status,
        )


class RequestCreate(BaseModel):
    task_name: str = Field(min_length=1, max_length=255)
    episodes_requested: int = Field(ge=1, le=10000)
    deadline: datetime
    notes: str | None = None


class RequestOut(BaseModel):
    id: int
    client_id: int
    client_name: str
    task_name: str
    episodes_requested: int
    deadline: datetime
    notes: str | None
    status: RequestStatus
    assigned_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StatusChange(BaseModel):
    status: RequestStatus


class AssignmentCreate(BaseModel):
    episode_ids: list[int] = Field(min_length=1)


class StatusHistoryOut(BaseModel):
    id: int
    from_status: RequestStatus | None
    to_status: RequestStatus
    changed_by_name: str
    changed_at: datetime


class ImportResult(BaseModel):
    imported: int
    skipped: int
    updated: int
    errors: list[str]


class AnalyticsQuery(BaseModel):
    start_date: datetime
    end_date: datetime


class EpisodesPerDay(BaseModel):
    date: str
    robot_id: str
    count: int


class RequestFulfilment(BaseModel):
    status_counts: dict[str, int]
    median_hours_submitted_to_delivered: float | None


class TopTask(BaseModel):
    task_name: str
    good_episode_count: int


class AnalyticsOut(BaseModel):
    episodes_per_day_per_robot: list[EpisodesPerDay]
    request_fulfilment: RequestFulfilment
    top_tasks_by_good_episodes: list[TopTask]
