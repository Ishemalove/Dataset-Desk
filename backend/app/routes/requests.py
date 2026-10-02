from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user, require_roles
from app.database import get_db
from app.models import Assignment, DatasetRequest, Episode, RequestStatus, StatusHistory, User, UserRole
from app.schemas import AssignmentCreate, EpisodeOut, RequestCreate, RequestOut, StatusChange, StatusHistoryOut
from app.services.export import enqueue_exports
from app.services.requests import DomainError, assign_episodes, transition_status

router = APIRouter(prefix="/requests", tags=["requests"])


def _serialize_request(req: DatasetRequest) -> RequestOut:
    return RequestOut(
        id=req.id,
        client_id=req.client_id,
        client_name=req.client.name,
        task_name=req.task_name,
        episodes_requested=req.episodes_requested,
        deadline=req.deadline,
        notes=req.notes,
        status=req.status,
        assigned_count=len(req.assignments),
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


@router.get("", response_model=list[RequestOut])
def list_requests(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(DatasetRequest).options(joinedload(DatasetRequest.client), joinedload(DatasetRequest.assignments))
    if user.role == UserRole.client:
        q = q.filter(DatasetRequest.client_id == user.id)
    requests = q.order_by(DatasetRequest.created_at.desc()).all()
    return [_serialize_request(r) for r in requests]


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: RequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.client)),
):
    req = DatasetRequest(
        client_id=user.id,
        task_name=payload.task_name.strip().lower(),
        episodes_requested=payload.episodes_requested,
        deadline=payload.deadline,
        notes=payload.notes,
        status=RequestStatus.submitted,
    )
    db.add(req)
    db.flush()
    db.add(StatusHistory(request_id=req.id, from_status=None, to_status=RequestStatus.submitted, changed_by=user.id))
    db.commit()
    db.refresh(req)
    req = (
        db.query(DatasetRequest)
        .options(joinedload(DatasetRequest.client), joinedload(DatasetRequest.assignments))
        .filter(DatasetRequest.id == req.id)
        .first()
    )
    return _serialize_request(req)


@router.get("/{request_id}", response_model=RequestOut)
def get_request(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    req = (
        db.query(DatasetRequest)
        .options(joinedload(DatasetRequest.client), joinedload(DatasetRequest.assignments))
        .filter(DatasetRequest.id == request_id)
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if user.role == UserRole.client and req.client_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return _serialize_request(req)


@router.post("/{request_id}/status", response_model=RequestOut)
def change_status(
    request_id: int,
    payload: StatusChange,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    req = db.get(DatasetRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    try:
        transition_status(db, req, payload.status, user)
    except DomainError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    req = (
        db.query(DatasetRequest)
        .options(joinedload(DatasetRequest.client), joinedload(DatasetRequest.assignments))
        .filter(DatasetRequest.id == request_id)
        .first()
    )
    return _serialize_request(req)


@router.get("/{request_id}/history", response_model=list[StatusHistoryOut])
def get_history(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    req = db.get(DatasetRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if user.role == UserRole.client and req.client_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    rows = (
        db.query(StatusHistory, User.name)
        .join(User, StatusHistory.changed_by == User.id)
        .filter(StatusHistory.request_id == request_id)
        .order_by(StatusHistory.changed_at)
        .all()
    )
    return [
        StatusHistoryOut(
            id=h.id,
            from_status=h.from_status,
            to_status=h.to_status,
            changed_by_name=name,
            changed_at=h.changed_at,
        )
        for h, name in rows
    ]


@router.get("/{request_id}/episodes", response_model=list[EpisodeOut])
def get_assigned_episodes(
    request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    req = db.get(DatasetRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if user.role == UserRole.client and req.client_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    assignments = (
        db.query(Assignment)
        .options(joinedload(Assignment.episode).joinedload(Episode.assignment))
        .filter(Assignment.request_id == request_id)
        .all()
    )
    return [EpisodeOut.from_episode(a.episode, assigned=True) for a in assignments]


@router.post("/{request_id}/assign", response_model=list[EpisodeOut])
def assign(
    request_id: int,
    payload: AssignmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operator, UserRole.admin)),
):
    req = db.get(DatasetRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    try:
        created = assign_episodes(db, req, payload.episode_ids, user)
    except DomainError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    enqueue_exports([a.id for a in created], background_tasks)
    assignments = (
        db.query(Assignment)
        .options(joinedload(Assignment.episode).joinedload(Episode.assignment))
        .filter(Assignment.request_id == request_id)
        .all()
    )
    return [EpisodeOut.from_episode(a.episode, assigned=True) for a in assignments]
