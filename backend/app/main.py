from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.auth import bootstrap_user
from app.core.config import settings
from app.db.session import SessionLocal

from app.models import UserRole

from app.routers import catalog
from app.routers.admin import router as admin_router
from app.routers.artwork import router as artwork_router
from app.routers.auth import router as auth_router
from app.routers.episodes import router as episodes_router
from app.routers.seasons import router as seasons_router
from app.routers.shows import router as shows_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()

    try:
        bootstrap_user(
            db,
            settings.admin_email.strip().lower(),
            settings.admin_password,
            UserRole.ADMIN,
        )

        bootstrap_user(
            db,
            settings.editor_email.strip().lower(),
            settings.editor_password,
            UserRole.EDITOR,
        )

        yield

    finally:
        db.close()


app = FastAPI(
    title="Peblo TV Mini",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(artwork_router)
app.include_router(shows_router)
app.include_router(seasons_router)
app.include_router(episodes_router)
app.include_router(catalog.router)


@app.get("/health")
def health():
    return {"status": "ok"}