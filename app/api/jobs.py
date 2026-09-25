from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, Template, GenerationJob, Certificate
from app.core.deps import get_current_user
from app.core.config import settings
from app.services.csv_service import parse_participants
from app.schemas.jobs import JobResponse
from app.tasks.generate import generate_job
router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("", response_model=JobResponse, status_code=202)
def create_job(background_tasks: BackgroundTasks, template_id: int = Form(...), participants: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if participants.content_type not in {"text/csv", "application/vnd.ms-excel", "application/octet-stream"}: raise HTTPException(400, "Participants file must be CSV")
    data = participants.file.read()
    try: rows = parse_participants(data, settings.max_batch_size)
    except ValueError as e: raise HTTPException(400, str(e))
    template = db.get(Template, template_id)
    if not template: raise HTTPException(404, "Template not found")
    job = GenerationJob(template_id=template.id, created_by=user.id, total=len(rows)); db.add(job); db.commit(); db.refresh(job)
    p = Path(settings.storage_dir) / "jobs"; p.mkdir(parents=True, exist_ok=True); csv_path = p / f"{job.id}_{uuid4().hex}.csv"; csv_path.write_bytes(data)
    background_tasks.add_task(generate_job, job.id, str(csv_path))
    return job

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job or job.created_by != user.id: raise HTTPException(404, "Job not found")
    return job

@router.get("/{job_id}/certificates")
def list_certificates(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job or job.created_by != user.id: raise HTTPException(404, "Job not found")
    return [{"id": c.id, "participant_id": c.participant_id, "name": c.participant_name, "email": c.email, "status": c.status, "download": f"/jobs/{job_id}/certificates/{c.id}/download"} for c in db.query(Certificate).filter(Certificate.job_id == job_id).all()]

@router.get("/{job_id}/certificates/{certificate_id}/download")
def download_certificate(job_id: int, certificate_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id); cert = db.get(Certificate, certificate_id)
    if not job or job.created_by != user.id or not cert or cert.job_id != job_id or cert.status != "generated": raise HTTPException(404, "Certificate not found")
    return FileResponse(cert.file_path, media_type="application/pdf", filename=f"{cert.participant_id}.pdf")
