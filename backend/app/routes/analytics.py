from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.database import get_db
from app.models import User, UserRole
from app.schemas import AnalyticsOut
from app.services.analytics import get_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsOut)
def analytics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.operator, UserRole.admin)),
):
    return get_analytics(db, start_date, end_date)
