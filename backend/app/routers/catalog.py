from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Artwork, Episode, Show

router = APIRouter(tags=["catalog"])


def build_catalogue_entries(db: Session):
    shows = (
        db.query(Show)
        .filter(Show.is_published.is_(True))
        .order_by(Show.section, Show.title, Show.id)
        .all()
    )

    catalogue = []

    for show in shows:
        episodes = (
            db.query(Episode)
            .join(Episode.season)
            .filter(
                Episode.is_published.is_(True),
                Episode.season.has(show_id=show.id),
            )
            .order_by(Episode.season_id, Episode.episode_number, Episode.id)
            .all()
        )

        grouped = {}

        for episode in episodes:
            group = grouped.setdefault(
                episode.content_group,
                {
                    "content_group": episode.content_group,
                    "episode_number": episode.episode_number,
                    "title": episode.title,
                    "synopsis": episode.synopsis,
                    "duration_seconds": episode.duration_seconds,
                    "languages": set(),
                    "season_number": episode.season.season_number,
                    "artwork": [],
                },
            )

            group["languages"].add(episode.language)

            artworks = (
                db.query(Artwork)
                .filter(Artwork.episode_id == episode.id)
                .order_by(Artwork.artwork_type, Artwork.id)
                .all()
            )

            for artwork in artworks:
                group["artwork"].append(
                    {
                        "type": artwork.artwork_type.value,
                        "storage_key": artwork.storage_key,
                        "width": artwork.width,
                        "height": artwork.height,
                    }
                )

        show_episodes = []

        for group in sorted(
            grouped.values(),
            key=lambda item: (
                item["season_number"],
                item["episode_number"],
                item["content_group"],
            ),
        ):
            group["languages"] = sorted(group["languages"])
            group["artwork"].sort(
                key=lambda item: (item["type"], item["storage_key"])
            )
            show_episodes.append(group)

        catalogue.append(
            {
                "id": show.id,
                "title": show.title,
                "synopsis": show.synopsis,
                "categories": sorted(show.categories or []),
                "section": show.section,
                "language": show.language,
                "episodes": show_episodes,
            }
        )

    return catalogue


@router.get("/catalog")
def get_catalog(db: Session = Depends(get_db)):
    return {
        "shows": build_catalogue_entries(db),
    }


@router.get("/catalog/search")
def search_catalog(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    language: str | None = Query(default=None),
    section: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    catalogue = build_catalogue_entries(db)

    results = []

    for show in catalogue:
        query_match = True
        category_match = True
        language_match = True
        section_match = True

        if q:
            query = q.strip().lower()

            show_match = query in show["title"].lower()

            category_text = " ".join(show["categories"]).lower()
            category_match = query in category_text or show_match

            episode_match = any(
                query in episode["title"].lower()
                or query in (episode["synopsis"] or "").lower()
                for episode in show["episodes"]
            )

            query_match = show_match or category_match or episode_match

        if category:
            category_match = category.lower() in {
                value.lower() for value in show["categories"]
            }

        if section:
            section_match = (
                show["section"] is not None
                and show["section"].lower() == section.lower()
            )

        if language:
            requested_language = language.lower()

            show_language_match = (
                show["language"].lower() == requested_language
            )

            episode_language_match = any(
                requested_language in {
                    value.lower() for value in episode["languages"]
                }
                for episode in show["episodes"]
            )

            language_match = show_language_match or episode_language_match

        if query_match and category_match and language_match and section_match:
            results.append(show)

    return {
        "query": q,
        "category": category,
        "language": language,
        "section": section,
        "count": len(results),
        "shows": results,
    }
    