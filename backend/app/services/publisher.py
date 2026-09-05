import json
import os
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Episode, PublishOutcome, PublishRun, Show
from app.services.validation import build_validation_report


BASE_DIR = Path(__file__).resolve().parents[2]
CATALOGUE_DIR = BASE_DIR / "storage"
CATALOGUE_FILE = CATALOGUE_DIR / "catalogue.json"


def build_catalogue(db: Session) -> dict:
    shows = (
        db.query(Show)
        .filter(Show.is_published.is_(True))
        .order_by(Show.section, Show.title, Show.id)
        .all()
    )

    grouped: dict[str, list[dict]] = defaultdict(list)

    for show in shows:
        episodes = (
            db.query(Episode)
            .join(Episode.season)
            .filter(
                Episode.is_published.is_(True),
                Episode.season.has(show_id=show.id),
            )
            .order_by(
                Episode.season_id,
                Episode.episode_number,
                Episode.language,
                Episode.id,
            )
            .all()
        )

        content_groups: dict[str, dict] = {}

        for episode in episodes:
            group = content_groups.setdefault(
                episode.content_group,
                {
                    "content_group": episode.content_group,
                    "episode_number": episode.episode_number,
                    "title": episode.title,
                    "synopsis": episode.synopsis,
                    "duration_seconds": episode.duration_seconds,
                    "season_number": episode.season.season_number,
                    "languages": [],
                    "artwork": [],
                },
            )

            if episode.language not in group["languages"]:
                group["languages"].append(episode.language)

            for artwork in episode.artworks:
                group["artwork"].append(
                    {
                        "type": artwork.artwork_type.value,
                        "storage_key": artwork.storage_key,
                    }
                )

        show_entry = {
            "id": show.id,
            "title": show.title,
            "synopsis": show.synopsis,
            "categories": show.categories,
            "section": show.section,
            "episodes": sorted(
                content_groups.values(),
                key=lambda item: (
                    item["season_number"],
                    item["episode_number"],
                    item["content_group"],
                ),
            ),
        }

        grouped[show.section].append(show_entry)

    sections = {
        section: sorted(
            entries,
            key=lambda item: (item["title"].lower(), item["id"]),
        )
        for section, entries in sorted(
            grouped.items(),
            key=lambda item: item[0].lower(),
        )
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sections": sections,
    }


def atomic_write_catalogue(catalogue: dict) -> None:
    CATALOGUE_DIR.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(
        prefix="catalogue-",
        suffix=".json.tmp",
        dir=CATALOGUE_DIR,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(
                catalogue,
                file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, CATALOGUE_FILE)

    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise


def publish_catalogue(
    db: Session,
    triggered_by_user_id: int | None = None,
) -> dict:
    started_at = datetime.now(timezone.utc)

    run = PublishRun(
        triggered_by_user_id=triggered_by_user_id,
        started_at=started_at,
        outcome=PublishOutcome.FAILED,
    )

    db.add(run)
    db.flush()

    validation = build_validation_report(db)

    if not validation["valid"]:
        run.completed_at = datetime.now(timezone.utc)
        run.outcome = PublishOutcome.FAILED
        run.error_message = (
            f"Validation failed with "
            f"{validation['issue_count']} issue(s)."
        )
        db.commit()

        return {
            "success": False,
            "publish_run_id": run.id,
            "validation": validation,
        }

    try:
        catalogue = build_catalogue(db)

        show_count = sum(
            len(entries)
            for entries in catalogue["sections"].values()
        )

        episode_count = sum(
            len(show["episodes"])
            for entries in catalogue["sections"].values()
            for show in entries
        )

        atomic_write_catalogue(catalogue)

        run.show_count = show_count
        run.episode_count = episode_count
        run.outcome = PublishOutcome.SUCCESS
        run.completed_at = datetime.now(timezone.utc)

        db.commit()

        return {
            "success": True,
            "publish_run_id": run.id,
            "show_count": show_count,
            "episode_count": episode_count,
            "catalogue_path": str(CATALOGUE_FILE),
        }

    except Exception as exc:
        db.rollback()

        # Re-open the failed run so the failure is still recorded.
        failed_run = db.get(PublishRun, run.id)

        if failed_run is not None:
            failed_run.completed_at = datetime.now(timezone.utc)
            failed_run.outcome = PublishOutcome.FAILED
            failed_run.error_message = str(exc)
            db.commit()

        raise