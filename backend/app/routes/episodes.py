from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.auth import require_roles
from app.database import get_db
from app.models import Assignment, Episode, EpisodeQuality, User, UserRole
from app.schemas import EpisodeOut, ImportResult
from app.services.import_episodes import import_episodes_csv

router = APIRouter(prefix="/episodes", tags=["episodes"])


@router.get("", response_model=list[EpisodeOut])
def list_episodes(
    task_name: str | None = Query(None),
    quality: EpisodeQuality | None = Query(None),
    unassigned_only: bool = Query(False),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.operator, UserRole.admin)),
):
    q = db.query(Episode).options(joinedload(Episode.assignment))
    if task_name:
        q = q.filter(Episode.task_name.ilike(f"%{task_name.strip().lower()}%"))
    if quality:
        q = q.filter(Episode.quality == quality)
    if unassigned_only:
        assigned_ids = db.query(Assignment.episode_id).subquery()
        q = q.filter(~Episode.id.in_(assigned_ids))
    episodes = q.order_by(Episode.recorded_at.desc()).limit(limit).all()
    return [EpisodeOut.from_episode(e) for e in episodes]


@router.post("/import", response_model=ImportResult)
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.operator, UserRole.admin)),
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    content = await file.read()
    result = import_episodes_csv(db, content)
    return ImportResult(**result)
