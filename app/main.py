from pathlib import Path
from fastapi import FastAPI
from app.core.config import settings
from app.db.session import Base, engine
from app.api.auth import router as auth_router
from app.api.templates import router as template_router
from app.api.jobs import router as jobs_router

app = FastAPI(title=settings.app_name, version="1.0.0")
Base.metadata.create_all(bind=engine)
Path(settings.storage_dir, "templates").mkdir(parents=True, exist_ok=True)
Path(settings.storage_dir, "certificates").mkdir(parents=True, exist_ok=True)
Path(settings.storage_dir, "jobs").mkdir(parents=True, exist_ok=True)
app.include_router(auth_router)
app.include_router(template_router)
app.include_router(jobs_router)

@app.get("/health")
def health(): return {"status":"ok"}
