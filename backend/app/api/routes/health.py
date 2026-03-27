from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import PipelineRun
from backend.app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health(db: Session = Depends(get_db)) -> dict[str, object]:
    latest_abs = db.scalars(
        select(PipelineRun)
        .where(PipelineRun.pipeline_name == "abs_ingestion")
        .where(PipelineRun.status == "completed")
        .order_by(PipelineRun.completed_at.desc())
    ).first()

    latest_metrics = db.scalars(
        select(PipelineRun)
        .where(PipelineRun.pipeline_name.in_(["suburb_metrics_ingestion", "manual_listing_ingestion"]))
        .where(PipelineRun.status == "completed")
        .order_by(PipelineRun.completed_at.desc())
    ).first()

    now = datetime.now(UTC)

    def _freshness_minutes(run: PipelineRun | None) -> int | None:
        if not run or not run.completed_at:
            return None
        completed = run.completed_at.replace(tzinfo=UTC) if run.completed_at.tzinfo is None else run.completed_at
        return max(0, int((now - completed).total_seconds() // 60))

    abs_minutes = _freshness_minutes(latest_abs)
    metrics_minutes = _freshness_minutes(latest_metrics)

    freshness_status = "degraded"
    freshest = min([value for value in [abs_minutes, metrics_minutes] if value is not None], default=None)
    if freshest is not None:
        if freshest < 72 * 60:
            freshness_status = "fresh"
        elif freshest < 14 * 24 * 60:
            freshness_status = "stale"

    return {
        "status": "ok",
        "freshness_status": freshness_status,
        "freshness_minutes": {
            "abs": abs_minutes,
            "metrics": metrics_minutes,
        },
    }
