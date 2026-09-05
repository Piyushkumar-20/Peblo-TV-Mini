import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models import Artwork, ArtworkType, Episode, Season, Show


BASE_DIR = Path(__file__).resolve().parents[2]
SEED_FILE = BASE_DIR / "seed" / "seed_shows.json"


def seed() -> None:
    with SEED_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    db = SessionLocal()

    try:
        show_map: dict[str, Show] = {}
        season_map: dict[tuple[int, int], Season] = {}

        for record in records:
            slug = record["slug"]

            # Show
            show = show_map.get(slug)

            if show is None:
                show = (
                    db.query(Show)
                    .filter(Show.title == record["show_title"])
                    .first()
                )

            if show is None:
                show = Show(
                    title=record["show_title"],
                    synopsis=record["synopsis"],
                    categories=record["categories"],
                    section=record["section"],
                    language=record["language"],
                    is_published=record["status"] == "published",
                )
                db.add(show)
                db.flush()

            show_map[slug] = show

            # Season
            season_key = (show.id, record["season_number"])
            season = season_map.get(season_key)

            if season is None:
                season = (
                    db.query(Season)
                    .filter(
                        Season.show_id == show.id,
                        Season.season_number == record["season_number"],
                    )
                    .first()
                )

            if season is None:
                season = Season(
                    show_id=show.id,
                    season_number=record["season_number"],
                )
                db.add(season)
                db.flush()

            season_map[season_key] = season

            # Episode
            existing_episode = (
                db.query(Episode)
                .filter(
                    Episode.content_group == record["content_group"],
                    Episode.language == record["language"],
                )
                .first()
            )

            if existing_episode is not None:
                continue

            episode = Episode(
                season_id=season.id,
                episode_number=record["episode_number"],
                title=record["episode_title"],
                synopsis=record["synopsis"],
                duration_seconds=record["duration_seconds"],
                language=record["language"],
                content_group=record["content_group"],
                is_published=record["status"] == "published",
            )

            db.add(episode)
            db.flush()

        db.commit()

        print(f"Seeded {len(records)} source records successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()