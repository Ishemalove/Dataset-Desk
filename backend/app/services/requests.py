from sqlalchemy.orm import Session, joinedload

from app.models import Assignment, DatasetRequest, Episode, EpisodeQuality, RequestStatus, StatusHistory, User, UserRole

VALID_TRANSITIONS: dict[tuple[RequestStatus, RequestStatus], set[UserRole]] = {
    (RequestStatus.submitted, RequestStatus.in_progress): {UserRole.operator, UserRole.admin},
    (RequestStatus.in_progress, RequestStatus.delivered): {UserRole.operator, UserRole.admin},
    (RequestStatus.delivered, RequestStatus.accepted): {UserRole.client, UserRole.admin},
    (RequestStatus.delivered, RequestStatus.rejected): {UserRole.client, UserRole.admin},
    (RequestStatus.rejected, RequestStatus.in_progress): {UserRole.operator, UserRole.admin},
}


class DomainError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def transition_status(db: Session, request: DatasetRequest, new_status: RequestStatus, user: User) -> DatasetRequest:
    current = request.status
    allowed_roles = VALID_TRANSITIONS.get((current, new_status))
    if allowed_roles is None:
        raise DomainError(f"Cannot transition from {current.value} to {new_status.value}")

    if user.role not in allowed_roles:
        raise DomainError("You do not have permission for this status change")

    if user.role == UserRole.client and request.client_id != user.id:
        raise DomainError("Clients can only act on their own requests")

    if new_status == RequestStatus.delivered:
        assigned = db.query(Assignment).filter(Assignment.request_id == request.id).count()
        if assigned < request.episodes_requested:
            raise DomainError(
                f"Need at least {request.episodes_requested} episodes assigned (currently {assigned})"
            )

    request.status = new_status
    db.add(
        StatusHistory(
            request_id=request.id,
            from_status=current,
            to_status=new_status,
            changed_by=user.id,
        )
    )
    db.commit()
    db.refresh(request)
    return request


def assign_episodes(db: Session, request: DatasetRequest, episode_ids: list[int], user: User) -> list[Assignment]:
    if user.role not in {UserRole.operator, UserRole.admin}:
        raise DomainError("Only operators can assign episodes")

    if request.status not in {RequestStatus.submitted, RequestStatus.in_progress, RequestStatus.rejected}:
        raise DomainError("Cannot assign episodes to a request in this status")

    episodes = (
        db.query(Episode)
        .options(joinedload(Episode.assignment))
        .filter(Episode.id.in_(episode_ids))
        .all()
    )

    if len(episodes) != len(set(episode_ids)):
        raise DomainError("One or more episodes not found")

    created: list[Assignment] = []
    for ep in episodes:
        if ep.quality == EpisodeQuality.bad:
            raise DomainError(f"Episode {ep.episode_id} has quality 'bad' and cannot be assigned")
        if ep.assignment is not None:
            raise DomainError(f"Episode {ep.episode_id} is already assigned to a request")

        assignment = Assignment(request_id=request.id, episode_id=ep.id, assigned_by=user.id)
        db.add(assignment)
        created.append(assignment)

    if request.status == RequestStatus.submitted:
        request.status = RequestStatus.in_progress
        db.add(
            StatusHistory(
                request_id=request.id,
                from_status=RequestStatus.submitted,
                to_status=RequestStatus.in_progress,
                changed_by=user.id,
            )
        )

    db.commit()
    return created
