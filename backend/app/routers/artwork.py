from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Artwork, ArtworkType, Episode
from app.storage.local import LocalStorage


router = APIRouter(
    prefix="/admin/artwork",
    tags=["artwork"],
)

storage = LocalStorage()

MAX_FILE_SIZE = 200 * 1024

EXPECTED_DIMENSIONS = {
    ArtworkType.POSTER: (600, 900),
    ArtworkType.BANNER: (1280, 720),
    ArtworkType.THUMBNAIL: (640, 360),
}


@router.post("/upload")
async def upload_artwork(
    episode_id: int,
    artwork_type: ArtworkType,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    episode = db.get(Episode, episode_id)

    if episode is None:
        raise HTTPException(
            status_code=404,
            detail=f"Episode {episode_id} not found.",
        )

    data = await file.read()

    if not data:
        raise HTTPException(
            status_code=400,
            detail="Artwork file is empty.",
        )

    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Artwork exceeds the 200 KB limit. "
                f"Received {len(data)} bytes."
            ),
        )

    try:
        image = Image.open(BytesIO(data))
        image.verify()

        image = Image.open(BytesIO(data))

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Invalid image file. Please upload a valid image.",
        )

    expected_width, expected_height = EXPECTED_DIMENSIONS[artwork_type]

    if image.size != (expected_width, expected_height):
        raise HTTPException(
            status_code=400,
            detail=(
                f"{artwork_type.value} artwork must be "
                f"{expected_width}x{expected_height}px. "
                f"Received {image.width}x{image.height}px."
            ),
        )

    extension = "jpg"

    if image.format == "PNG":
        extension = "png"
    elif image.format == "WEBP":
        extension = "webp"
    elif image.format in {"JPEG", "JPG"}:
        extension = "jpg"

    key = (
        f"episodes/{episode_id}/"
        f"{artwork_type.value}/"
        f"{uuid4().hex}.{extension}"
    )

    storage.save(key, data)

    existing = (
        db.query(Artwork)
        .filter(
            Artwork.episode_id == episode_id,
            Artwork.artwork_type == artwork_type,
        )
        .all()
    )

    for artwork in existing:
        storage.delete(artwork.storage_key)
        db.delete(artwork)

    artwork = Artwork(
        episode_id=episode_id,
        artwork_type=artwork_type,
        storage_key=key,
        width=image.width,
        height=image.height,
        file_size_bytes=len(data),
    )

    db.add(artwork)
    db.commit()
    db.refresh(artwork)

    return {
        "id": artwork.id,
        "episode_id": artwork.episode_id,
        "artwork_type": artwork.artwork_type.value,
        "storage_key": artwork.storage_key,
        "width": artwork.width,
        "height": artwork.height,
        "file_size_bytes": artwork.file_size_bytes,
    }