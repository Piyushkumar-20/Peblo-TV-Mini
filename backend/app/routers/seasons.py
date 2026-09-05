from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Season, Show
from app.schemas import SeasonCreate, SeasonRead, SeasonUpdate


router = APIRouter(
    prefix="/admin",
    tags=["seasons"],
)


@router.get(
    "/shows/{show_id}/seasons",
    response_model=list[SeasonRead],
)
def list_seasons(
    show_id: int,
    db: Session = Depends(get_db),
):
    show = db.get(Show, show_id)

    if show is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found.",
        )

    return (
        db.query(Season)
        .filter(Season.show_id == show_id)
        .order_by(Season.season_number.asc())
        .all()
    )


@router.post(
    "/shows/{show_id}/seasons",
    response_model=SeasonRead,
    status_code=status.HTTP_201_CREATED,
)
def create_season(
    show_id: int,
    payload: SeasonCreate,
    db: Session = Depends(get_db),
):
    show = db.get(Show, show_id)

    if show is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found.",
        )

    season = Season(
        show_id=show_id,
        season_number=payload.season_number,
    )

    db.add(season)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Season {payload.season_number} already exists "
                f"for this show."
            ),
        )

    db.refresh(season)

    return season


@router.patch(
    "/seasons/{season_id}",
    response_model=SeasonRead,
)
def update_season(
    season_id: int,
    payload: SeasonUpdate,
    db: Session = Depends(get_db),
):
    season = db.get(Season, season_id)

    if season is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Season not found.",
        )

    if payload.season_number is not None:
        season.season_number = payload.season_number

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Season {season.season_number} already exists "
                f"for this show."
            ),
        )

    db.refresh(season)

    return season


@router.delete(
    "/seasons/{season_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_season(
    season_id: int,
    db: Session = Depends(get_db),
):
    season = db.get(Season, season_id)

    if season is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Season not found.",
        )

    db.delete(season)
    db.commit()

    return None