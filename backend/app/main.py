from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import search, verify, images, models

app = FastAPI(
    title="Jo Yuri Image Recognition",
    description="Semantic search and face verification for Jo Yuri images",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(verify.router, prefix="/api/verify", tags=["verify"])
app.include_router(models.router, prefix="/api/models", tags=["models"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
