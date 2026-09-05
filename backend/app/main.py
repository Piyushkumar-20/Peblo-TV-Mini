from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.auth import bootstrap_user
from app.core.config import settings
from app.db.session import SessionLocal

from app.routers import admin
from app.routers import artwork
from app.routers import auth
from app.routers import episodes
from app.routers import seasons
from app.routers import shows
from app.routers import catalog

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()

    try:
        bootstrap_user(
            db=db,
            email=settings.admin_email,
            password=settings.admin_password,
            role="admin",
        )

        bootstrap_user(
            db=db,
            email=settings.editor_email,
            password=settings.editor_password,
            role="editor",
        )

        db.commit()
    finally:
        db.close()

    yield


app = FastAPI(
    title="Peblo TV Mini API",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(shows.router)
app.include_router(seasons.router)
app.include_router(episodes.router)
app.include_router(artwork.router)
app.include_router(catalog.router)

@app.get("/health")
def health():
    return {"status": "ok"}