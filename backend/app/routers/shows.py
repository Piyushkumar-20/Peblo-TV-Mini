from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Show
from app.schemas import ShowCreate, ShowRead, ShowUpdate


router = APIRouter(
    prefix="/admin/shows",
    tags=["shows"],
)


@router.get("", response_model=list[ShowRead])
def list_shows(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    section: str | None = Query(default=None),
    language: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Show)

    if q:
        search = f"%{q.strip()}%"

        query = query.filter(
            or_(
                Show.title.ilike(search),
                Show.synopsis.ilike(search),
            )
        )

    if category:
        query = query.filter(
            Show.categories.contains([category])
        )

    if section:
        query = query.filter(
            func.lower(Show.section) == section.lower()
        )

    if language:
        query = query.filter(
            func.lower(Show.language) == language.lower()
        )

    offset = (page - 1) * page_size

    return (
        query
        .order_by(Show.title.asc(), Show.id.asc())
        .offset(offset)
        .limit(page_size)
        .all()
    )


@router.post(
    "",
    response_model=ShowRead,
    status_code=status.HTTP_201_CREATED,
)
def create_show(
    payload: ShowCreate,
    db: Session = Depends(get_db),
):
    if payload.is_published and not payload.section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A published show must have a section.",
        )

    show = Show(
        title=payload.title,
        synopsis=payload.synopsis,
        categories=payload.categories,
        section=payload.section,
        language=payload.language,
        is_published=payload.is_published,
    )

    db.add(show)
    db.commit()
    db.refresh(show)

    return show


@router.get(
    "/{show_id}",
    response_model=ShowRead,
)
def get_show(
    show_id: int,
    db: Session = Depends(get_db),
):
    show = db.get(Show, show_id)

    if show is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found.",
        )

    return show


@router.patch(
    "/{show_id}",
    response_model=ShowRead,
)
def update_show(
    show_id: int,
    payload: ShowUpdate,
    db: Session = Depends(get_db),
):
    show = db.get(Show, show_id)

    if show is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found.",
        )

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(show, field, value)

    if show.is_published and not show.section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A published show must have a section.",
        )

    db.commit()
    db.refresh(show)

    return show


@router.delete(
    "/{show_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_show(
    show_id: int,
    db: Session = Depends(get_db),
):
    show = db.get(Show, show_id)

    if show is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found.",
        )

    db.delete(show)
    db.commit()

    return None