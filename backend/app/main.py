from fastapi import FastAPI

from app.routers.admin import router as admin_router
from app.routers.artwork import router as artwork_router


app = FastAPI(title="Peblo TV Mini")

app.include_router(admin_router)
app.include_router(artwork_router)


@app.get("/health")
def health():
    return {"status": "ok"}