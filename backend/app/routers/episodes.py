from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Artwork, Episode, Season
from app.schemas import EpisodeCreate, EpisodeRead, EpisodeUpdate


router = APIRouter(
    prefix="/admin",
    tags=["episodes"],
)


def validate_season_zero(season: Season, title: str) -> None:
    """Season 0 is reserved exclusively for trailers."""
    if season.season_number == 0 and "trailer" not in title.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Season 0 is reserved for trailers. "
                "The episode title must contain 'Trailer'."
            ),
        )


def validate_episode_for_publish(
    episode: Episode,
    db: Session,
) -> None:
    """Validate requirements for publishing an episode."""

    if not episode.duration_seconds or episode.duration_seconds <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A published episode must have a valid "
                "duration_seconds greater than 0."
            ),
        )

    artwork_count = (
        db.query(Artwork)
        .filter(Artwork.episode_id == episode.id)
        .count()
    )

    if artwork_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A published episode must have at least one artwork.",
        )


def handle_integrity_error(exc: IntegrityError) -> None:
    error_message = str(exc.orig)

    if "uq_episode_content_group_language" in error_message:
        detail = (
            "An episode with this content_group and language "
            "already exists."
        )
    else:
        detail = "Episode could not be saved."

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
    )


@router.get(
    "/seasons/{season_id}/episodes",
    response_model=list[EpisodeRead],
)
def list_episodes(
    season_id: int,
    db: Session = Depends(get_db),
):
    season = db.get(Season, season_id)

    if season is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Season not found.",
        )

    return (
        db.query(Episode)
        .filter(Episode.season_id == season_id)
        .order_by(
            Episode.episode_number.asc(),
            Episode.id.asc(),
        )
        .all()
    )


@router.post(
    "/seasons/{season_id}/episodes",
    response_model=EpisodeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_episode(
    season_id: int,
    payload: EpisodeCreate,
    db: Session = Depends(get_db),
):
    season = db.get(Season, season_id)

    if season is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Season not found.",
        )

    validate_season_zero(
        season,
        payload.title,
    )

    episode = Episode(
        season_id=season_id,
        episode_number=payload.episode_number,
        title=payload.title,
        synopsis=payload.synopsis,
        duration_seconds=payload.duration_seconds,
        language=payload.language,
        content_group=payload.content_group,
        is_published=False,
    )

    db.add(episode)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        handle_integrity_error(exc)

    db.refresh(episode)

    return episode


@router.get(
    "/episodes/{episode_id}",
    response_model=EpisodeRead,
)
def get_episode(
    episode_id: int,
    db: Session = Depends(get_db),
):
    episode = db.get(Episode, episode_id)

    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found.",
        )

    return episode


@router.patch(
    "/episodes/{episode_id}",
    response_model=EpisodeRead,
)
def update_episode(
    episode_id: int,
    payload: EpisodeUpdate,
    db: Session = Depends(get_db),
):
    episode = db.get(Episode, episode_id)

    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found.",
        )

    updates = payload.model_dump(exclude_unset=True)

    season = db.get(Season, episode.season_id)

    if season is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode season not found.",
        )

    new_title = updates.get("title", episode.title)

    validate_season_zero(
        season,
        new_title,
    )

    for field, value in updates.items():
        setattr(episode, field, value)

    if episode.is_published:
        validate_episode_for_publish(
            episode,
            db,
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        handle_integrity_error(exc)

    db.refresh(episode)

    return episode


@router.delete(
    "/episodes/{episode_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_episode(
    episode_id: int,
    db: Session = Depends(get_db),
):
    episode = db.get(Episode, episode_id)

    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found.",
        )

    db.delete(episode)
    db.commit()

    return None