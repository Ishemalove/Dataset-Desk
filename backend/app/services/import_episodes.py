import csv
import io
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Episode, EpisodeQuality

KNOWN_ROBOTS = {"arm-01", "arm-02", "arm-03", "mobile-01", "humanoid-01"}
VALID_QUALITIES = {"good", "usable", "bad"}
MAX_DURATION = 600  # 10 minutes
MIN_DATE = datetime(2020, 1, 1, tzinfo=timezone.utc)
MAX_DATE = datetime(2028, 12, 31, tzinfo=timezone.utc)


def _normalize_episode_id(raw: str) -> str | None:
    if not raw or not raw.strip():
        return None
    return raw.strip().upper()


def _normalize_task_name(raw: str) -> str | None:
    if not raw or not raw.strip():
        return None
    return re.sub(r"\s+", " ", raw.strip().lower())


def _parse_date(raw: str) -> datetime | None:
    if not raw or not raw.strip():
        return None
    value = raw.strip().replace("Z", "+00:00")
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _parse_duration(raw: str) -> int | None:
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip().upper()
    if text in {"N/A", "NA", ""}:
        return None
    try:
        val = int(float(text))
    except ValueError:
        return None
    if val < 1 or val > MAX_DURATION:
        return None
    return val


def _parse_quality(raw: str) -> EpisodeQuality | None:
    if not raw or not str(raw).strip():
        return None
    val = str(raw).strip().lower()
    if val == "excellent":
        val = "good"
    if val not in VALID_QUALITIES:
        return None
    return EpisodeQuality(val)


def import_episodes_csv(db: Session, content: str | bytes) -> dict:
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(content))
    imported = 0
    updated = 0
    skipped = 0
    errors: list[str] = []
    seen_in_file: set[str] = set()

    for row_num, row in enumerate(reader, start=2):
        episode_id = _normalize_episode_id(row.get("episode_id", ""))
        if not episode_id:
            skipped += 1
            errors.append(f"Row {row_num}: missing episode_id")
            continue

        if episode_id in seen_in_file:
            skipped += 1
            errors.append(f"Row {row_num}: duplicate episode_id {episode_id} in file")
            continue
        seen_in_file.add(episode_id)

        robot_id = (row.get("robot_id") or "").strip()
        if not robot_id or robot_id not in KNOWN_ROBOTS:
            skipped += 1
            errors.append(f"Row {row_num}: invalid or unknown robot_id '{robot_id}'")
            continue

        task_name = _normalize_task_name(row.get("task_name", ""))
        if not task_name or "," in task_name:
            skipped += 1
            errors.append(f"Row {row_num}: invalid task_name")
            continue

        recorded_at = _parse_date(row.get("recorded_at", ""))
        if recorded_at is None or recorded_at < MIN_DATE or recorded_at > MAX_DATE:
            skipped += 1
            errors.append(f"Row {row_num}: invalid recorded_at")
            continue

        duration = _parse_duration(row.get("duration_seconds", ""))
        if duration is None:
            skipped += 1
            errors.append(f"Row {row_num}: invalid duration_seconds")
            continue

        operator_name = (row.get("operator_name") or "").strip()
        if not operator_name:
            skipped += 1
            errors.append(f"Row {row_num}: missing operator_name")
            continue

        quality = _parse_quality(row.get("quality", ""))
        if quality is None:
            skipped += 1
            errors.append(f"Row {row_num}: invalid quality")
            continue

        existing = db.query(Episode).filter(Episode.episode_id == episode_id).first()
        if existing:
            changed = False
            for field, val in [
                ("robot_id", robot_id),
                ("task_name", task_name),
                ("recorded_at", recorded_at),
                ("duration_seconds", duration),
                ("operator_name", operator_name),
                ("quality", quality),
            ]:
                if getattr(existing, field) != val:
                    setattr(existing, field, val)
                    changed = True
            if changed:
                updated += 1
            else:
                skipped += 1
                errors.append(f"Row {row_num}: episode {episode_id} already exists (unchanged)")
            continue

        db.add(
            Episode(
                episode_id=episode_id,
                robot_id=robot_id,
                task_name=task_name,
                recorded_at=recorded_at,
                duration_seconds=duration,
                operator_name=operator_name,
                quality=quality,
            )
        )
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "updated": updated, "errors": errors[:100]}
