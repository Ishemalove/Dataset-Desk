import logging
import random
import time

from app.config import settings
from app.database import SessionLocal
from app.models import Assignment, ExportStatus

logger = logging.getLogger("dataset_desk")

MAX_ATTEMPTS = 3


def run_episode_export(assignment_id: int) -> None:
    """Simulate an idempotent export job with retries. Persists status in Postgres."""
    db = SessionLocal()
    try:
        assignment = db.get(Assignment, assignment_id)
        if assignment is None:
            return
        if assignment.export_status == ExportStatus.done.value:
            return

        while assignment.export_attempts < MAX_ATTEMPTS:
            if assignment.export_status == ExportStatus.done.value:
                return
            assignment.export_status = ExportStatus.running.value
            assignment.export_attempts += 1
            db.commit()

            time.sleep(random.uniform(2, 5))
            db.refresh(assignment)

            if random.random() >= 0.2:
                assignment.export_status = ExportStatus.done.value
                db.commit()
                logger.info("Export succeeded for assignment %s", assignment_id)
                return

            assignment.export_status = ExportStatus.failed.value
            db.commit()
            logger.warning(
                "Export failed for assignment %s (attempt %s)",
                assignment_id,
                assignment.export_attempts,
            )

        logger.error("Export gave up for assignment %s", assignment_id)
    except Exception:
        logger.exception("Export crashed for assignment %s", assignment_id)
        db.rollback()
        assignment = db.get(Assignment, assignment_id)
        if assignment is not None and assignment.export_status != ExportStatus.done.value:
            assignment.export_status = ExportStatus.failed.value
            db.commit()
    finally:
        db.close()


def enqueue_exports(assignment_ids: list[int], background_tasks) -> None:
    if not settings.enable_export_jobs:
        return
    for aid in assignment_ids:
        background_tasks.add_task(run_episode_export, aid)
