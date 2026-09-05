from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.validation import build_validation_report
from app.services.publisher import publish_catalogue

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

@router.post("/catalog/publish")
def publish_catalog(
    db: Session = Depends(get_db),
):
    return publish_catalogue(db)