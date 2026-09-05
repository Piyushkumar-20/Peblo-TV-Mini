from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ArtworkType, Episode, Season, Show


MAX_ARTWORK_SIZE_BYTES = 200 * 1024

EXPECTED_ARTWORK_DIMENSIONS = {
    ArtworkType.POSTER: (600, 900),
    ArtworkType.BANNER: (1280, 720),
    ArtworkType.THUMBNAIL: (640, 360),
}


@dataclass
class ValidationIssue:
    entity_type: str
    entity_id: int
    code: str
    message: str

    def as_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "code": self.code,
            "message": self.message,
        }


def validate_show(show: Show) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not show.section:
        issues.append(
            ValidationIssue(
                entity_type="show",
                entity_id=show.id,
                code="missing_section",
                message="Published show must have a section.",
            )
        )

    return issues


def validate_episode(
    episode: Episode,
    season: Season,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not episode.is_published:
        return issues

    if episode.duration_seconds is None or episode.duration_seconds <= 0:
        issues.append(
            ValidationIssue(
                entity_type="episode",
                entity_id=episode.id,
                code="missing_duration",
                message="Published episode must have a valid duration.",
            )
        )

    if not episode.artworks:
        issues.append(
            ValidationIssue(
                entity_type="episode",
                entity_id=episode.id,
                code="missing_artwork",
                message="Published episode must have artwork.",
            )
        )

    for artwork in episode.artworks:
        expected = EXPECTED_ARTWORK_DIMENSIONS.get(artwork.artwork_type)

        if expected is None:
            issues.append(
                ValidationIssue(
                    entity_type="artwork",
                    entity_id=artwork.id,
                    code="invalid_artwork_type",
                    message=f"Unsupported artwork type: {artwork.artwork_type}.",
                )
            )
            continue

        expected_width, expected_height = expected

        if (
            artwork.width != expected_width
            or artwork.height != expected_height
        ):
            issues.append(
                ValidationIssue(
                    entity_type="artwork",
                    entity_id=artwork.id,
                    code="invalid_artwork_dimensions",
                    message=(
                        f"{artwork.artwork_type.value} artwork must be "
                        f"{expected_width}x{expected_height}px; "
                        f"got {artwork.width}x{artwork.height}px."
                    ),
                )
            )

        if artwork.file_size_bytes > MAX_ARTWORK_SIZE_BYTES:
            issues.append(
                ValidationIssue(
                    entity_type="artwork",
                    entity_id=artwork.id,
                    code="artwork_too_large",
                    message=(
                        "Artwork must be no larger than 200 KB; "
                        f"got {artwork.file_size_bytes} bytes."
                    ),
                )
            )

    if season.season_number == 0:
        normalized_title = episode.title.strip().lower()

        if "trailer" not in normalized_title:
            issues.append(
                ValidationIssue(
                    entity_type="episode",
                    entity_id=episode.id,
                    code="invalid_season_zero",
                    message="Season 0 is reserved for trailers.",
                )
            )

    return issues


def validate_duplicate_content_groups(
    db: Session,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    rows = (
        db.query(
            Episode.content_group,
            Episode.language,
        )
        .group_by(
            Episode.content_group,
            Episode.language,
        )
        .having(func.count(Episode.id) > 1)
        .all()
    )

    for content_group, language in rows:
        issues.append(
            ValidationIssue(
                entity_type="episode",
                entity_id=0,
                code="duplicate_content_group_language",
                message=(
                    "Duplicate episode variant for "
                    f"content_group='{content_group}', language='{language}'."
                ),
            )
        )

    return issues


def build_validation_report(db: Session) -> dict:
    issues: list[ValidationIssue] = []

    shows = db.query(Show).all()

    for show in shows:
        if show.is_published:
            issues.extend(validate_show(show))

        for season in show.seasons:
            for episode in season.episodes:
                issues.extend(validate_episode(episode, season))

    issues.extend(validate_duplicate_content_groups(db))

    return {
        "valid": len(issues) == 0,
        "issue_count": len(issues),
        "issues": [issue.as_dict() for issue in issues],
    }