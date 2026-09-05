from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Artwork, ArtworkType, Episode
from app.storage.local import LocalStorage


router = APIRouter(tags=["artwork"])

storage = LocalStorage()

MAX_ARTWORK_SIZE_BYTES = 200 * 1024

EXPECTED_DIMENSIONS = {
    ArtworkType.POSTER: (600, 900),
    ArtworkType.BANNER: (1280, 720),
    ArtworkType.THUMBNAIL: (640, 360),
}


@router.post("/admin/artwork/upload")
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

    if len(data) > MAX_ARTWORK_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Artwork exceeds the 200 KB limit. "
                f"Received {len(data)} bytes."
            ),
        )

    try:
        image = Image.open(BytesIO(data))
        image.verify()

        # Re-open after verify() because verify() invalidates the image object.
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

    if image.format == "PNG":
        extension = "png"
    elif image.format == "WEBP":
        extension = "webp"
    else:
        extension = "jpg"

    storage_key = (
        f"episodes/{episode_id}/"
        f"{artwork_type.value}/"
        f"{uuid4().hex}.{extension}"
    )

    # Replace the existing artwork for this slot.
    existing_artworks = (
        db.query(Artwork)
        .filter(
            Artwork.episode_id == episode_id,
            Artwork.artwork_type == artwork_type,
        )
        .all()
    )

    for existing in existing_artworks:
        storage.delete(existing.storage_key)
        db.delete(existing)

    storage.save(storage_key, data)

    artwork = Artwork(
        episode_id=episode_id,
        artwork_type=artwork_type,
        storage_key=storage_key,
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
        "url": f"/catalog/artwork/{artwork.storage_key}",
    }


@router.get("/catalog/artwork/{storage_key:path}")
def get_artwork(storage_key: str):
    try:
        path = storage.get_path(storage_key)
    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail="Artwork not found.",
        ) from exc

    if not path.exists() or not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Artwork not found.",
        )

    return FileResponse(path)