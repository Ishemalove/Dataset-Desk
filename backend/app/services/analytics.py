from datetime import datetime

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models import DatasetRequest, Episode, EpisodeQuality


def get_analytics(db: Session, start_date: datetime, end_date: datetime) -> dict:
    dialect = db.get_bind().dialect.name

    if dialect == "postgresql":
        episodes_per_day = db.execute(
            text("""
                SELECT DATE(recorded_at AT TIME ZONE 'UTC') AS day, robot_id, COUNT(*) AS cnt
                FROM episodes
                WHERE recorded_at >= :start AND recorded_at <= :end
                GROUP BY day, robot_id
                ORDER BY day, robot_id
            """),
            {"start": start_date, "end": end_date},
        ).mappings().all()

        median_row = db.execute(
            text("""
                WITH delivery_times AS (
                    SELECT EXTRACT(EPOCH FROM (del.changed_at - sub.created_at)) / 3600.0 AS hours
                    FROM dataset_requests sub
                    JOIN status_history del ON del.request_id = sub.id AND del.to_status = 'delivered'
                    WHERE sub.created_at >= :start AND sub.created_at <= :end
                )
                SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hours) AS median_hours
                FROM delivery_times
            """),
            {"start": start_date, "end": end_date},
        ).first()
        median_hours = (
            float(median_row.median_hours)
            if median_row and median_row.median_hours is not None
            else None
        )
    else:
        # SQLite-compatible fallback for local/dev (production uses PostgreSQL)
        episodes_per_day = db.execute(
            text("""
                SELECT DATE(recorded_at) AS day, robot_id, COUNT(*) AS cnt
                FROM episodes
                WHERE recorded_at >= :start AND recorded_at <= :end
                GROUP BY day, robot_id
                ORDER BY day, robot_id
            """),
            {"start": start_date, "end": end_date},
        ).mappings().all()

        hours = db.execute(
            text("""
                SELECT (julianday(del.changed_at) - julianday(sub.created_at)) * 24.0 AS hours
                FROM dataset_requests sub
                JOIN status_history del ON del.request_id = sub.id AND del.to_status = 'delivered'
                WHERE sub.created_at >= :start AND sub.created_at <= :end
                ORDER BY hours
            """),
            {"start": start_date, "end": end_date},
        ).scalars().all()
        if hours:
            mid = len(hours) // 2
            median_hours = float(hours[mid]) if len(hours) % 2 == 1 else (float(hours[mid - 1]) + float(hours[mid])) / 2
        else:
            median_hours = None

    status_counts = dict(
        db.query(DatasetRequest.status, func.count())
        .group_by(DatasetRequest.status)
        .all()
    )

    top_tasks = (
        db.query(Episode.task_name, func.count().label("cnt"))
        .filter(Episode.quality == EpisodeQuality.good)
        .filter(Episode.recorded_at >= start_date, Episode.recorded_at <= end_date)
        .group_by(Episode.task_name)
        .order_by(func.count().desc())
        .limit(5)
        .all()
    )

    return {
        "episodes_per_day_per_robot": [
            {"date": str(r["day"]), "robot_id": r["robot_id"], "count": r["cnt"]}
            for r in episodes_per_day
        ],
        "request_fulfilment": {
            "status_counts": {k.value if hasattr(k, "value") else k: v for k, v in status_counts.items()},
            "median_hours_submitted_to_delivered": median_hours,
        },
        "top_tasks_by_good_episodes": [
            {"task_name": name, "good_episode_count": cnt} for name, cnt in top_tasks
        ],
    }
