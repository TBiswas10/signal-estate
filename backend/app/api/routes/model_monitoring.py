from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_admin_user
from backend.app.db.models import ModelEvaluation, User
from backend.app.db.session import get_db
from backend.app.schemas import ModelEvaluationCreateRequest, ModelEvaluationOut

router = APIRouter(prefix="/models", tags=["model-monitoring"])


@router.post("/evaluations", response_model=ModelEvaluationOut)
def create_evaluation(
    payload: ModelEvaluationCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> ModelEvaluationOut:
    row = ModelEvaluation(
        model_name=payload.model_name,
        model_version=payload.model_version,
        split_name=payload.split_name,
        mae=payload.mae,
        rmse=payload.rmse,
        mape=payload.mape,
        drift_score=payload.drift_score,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ModelEvaluationOut(
        id=row.id,
        model_name=row.model_name,
        model_version=row.model_version,
        split_name=row.split_name,
        mae=row.mae,
        rmse=row.rmse,
        mape=row.mape,
        drift_score=row.drift_score,
    )


@router.get("/evaluations", response_model=list[ModelEvaluationOut])
def list_evaluations(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> list[ModelEvaluationOut]:
    rows = db.scalars(select(ModelEvaluation).order_by(desc(ModelEvaluation.created_at)).limit(200)).all()
    return [
        ModelEvaluationOut(
            id=row.id,
            model_name=row.model_name,
            model_version=row.model_version,
            split_name=row.split_name,
            mae=row.mae,
            rmse=row.rmse,
            mape=row.mape,
            drift_score=row.drift_score,
        )
        for row in rows
    ]
