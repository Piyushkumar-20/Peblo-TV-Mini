from fastapi import FastAPI  

app = FastAPI(title="Peblo TV Mini")


@app.get("/health")
def health():
    return {"status": "ok"}