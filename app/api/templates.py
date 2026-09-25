from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, Template
from app.core.deps import get_current_user
from app.core.config import settings
from PIL import Image
router = APIRouter(prefix="/templates", tags=["templates"])

@router.post("")
def upload_template(name: str = Form(...), file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if file.content_type not in {"image/png", "image/jpeg"}: raise HTTPException(400, "Template must be PNG or JPEG")
    data = file.file.read()
    if len(data) > 10 * 1024 * 1024: raise HTTPException(413, "Template must be <= 10MB")
    try:
        img = Image.open(__import__('io').BytesIO(data)); img.verify()
    except Exception: raise HTTPException(400, "Invalid image template")
    ext = ".png" if file.content_type == "image/png" else ".jpg"
    path = Path(settings.storage_dir) / "templates" / f"{uuid4().hex}{ext}"; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    t = Template(name=name, filename=str(path), content_type=file.content_type, created_by=user.id); db.add(t); db.commit(); db.refresh(t)
    return {"id": t.id, "name": t.name}
