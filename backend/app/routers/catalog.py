import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["catalog"])

BASE_DIR = Path(__file__).resolve().parents[2]
CATALOGUE_FILE = BASE_DIR / "storage" / "catalogue.json"


def read_published_catalogue() -> dict:
    if not CATALOGUE_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail="No published catalogue is available yet.",
        )

    try:
        with CATALOGUE_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Published catalogue is unavailable.",
        ) from exc


def catalogue_shows(catalogue: dict) -> list[dict]:
    shows = []

    for entries in catalogue.get("sections", {}).values():
        shows.extend(entries)

    return shows


@router.get("/catalog")
def get_catalog():
    return read_published_catalogue()


@router.get("/catalog/search")
def search_catalog(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    language: str | None = Query(default=None),
    section: str | None = Query(default=None),
):
    catalogue = read_published_catalogue()
    shows = catalogue_shows(catalogue)

    query = q.strip().lower() if q else None
    requested_category = category.strip().lower() if category else None
    requested_language = language.strip().lower() if language else None
    requested_section = section.strip().lower() if section else None

    results = []

    for show in shows:
        categories = {
            value.lower()
            for value in (show.get("categories") or [])
        }

        show_language = (show.get("language") or "").lower()
        show_section = (show.get("section") or "").lower()

        episodes = show.get("episodes") or []

        query_match = True
        category_match = True
        language_match = True
        section_match = True

        if query:
            show_title_match = query in show["title"].lower()

            category_match_for_query = any(
                query in value
                for value in categories
            )

            episode_title_match = any(
                query in (episode.get("title") or "").lower()
                for episode in episodes
            )

            query_match = (
                show_title_match
                or category_match_for_query
                or episode_title_match
            )

        if requested_category:
            category_match = requested_category in categories

        if requested_language:
            episode_language_match = any(
                requested_language in {
                    value.lower()
                    for value in (episode.get("languages") or [])
                }
                for episode in episodes
            )

            language_match = (
                show_language == requested_language
                or episode_language_match
            )

        if requested_section:
            section_match = show_section == requested_section

        if (
            query_match
            and category_match
            and language_match
            and section_match
        ):
            results.append(show)

    return {
        "query": q,
        "category": category,
        "language": language,
        "section": section,
        "count": len(results),
        "shows": results,
    }