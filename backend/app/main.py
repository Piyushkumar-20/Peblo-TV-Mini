from fastapi import FastAPI

from app.routers.admin import router as admin_router
from app.routers.artwork import router as artwork_router
from app.routers.shows import router as shows_router
from app.routers.seasons import router as seasons_router
from app.routers.episodes import router as episodes_router

app = FastAPI(title="Peblo TV Mini", version="0.1.0")

app.include_router(admin_router)
app.include_router(artwork_router)
app.include_router(shows_router)
app.include_router(seasons_router)
app.include_router(episodes_router)

@app.get("/health")
def health():
    return {"status": "ok"}