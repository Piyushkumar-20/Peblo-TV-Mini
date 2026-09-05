from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require_admin, require_editor
from app.db.session import get_db
from app.models import User
from app.services.publisher import publish_catalogue
from app.services.validation import build_validation_report

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/validation-report")
def validation_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor),
):
    return build_validation_report(db)


@router.post("/catalog/publish")
def publish_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return publish_catalogue(
        db,
        triggered_by_user_id=current_user.id,
    )