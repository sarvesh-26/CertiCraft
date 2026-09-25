"""Background certificate generation.

This assignment runs without Docker, Redis, or Celery by default. FastAPI's
BackgroundTasks executes this function after the HTTP response is returned,
so the client does not need to keep the request open for the whole batch.
"""
from datetime import datetime, timezone
from pathlib import Path
import logging

from app.db.session import SessionLocal
from app.models import GenerationJob, Template, Certificate
from app.services.csv_service import parse_participants
from app.services.certificate_service import generate_certificate
from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_job(job_id: int, csv_path: str) -> None:
    """Generate all certificates for a job in a background task."""
    db = SessionLocal()
    job = db.get(GenerationJob, job_id)
    if not job:
        db.close()
        logger.error("Generation job %s not found", job_id)
        return

    try:
        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        template = db.get(Template, job.template_id)
        if not template:
            raise RuntimeError("Certificate template no longer exists")

        rows = parse_participants(Path(csv_path).read_bytes(), settings.max_batch_size)
        job.total = len(rows)
        db.commit()

        out_dir = Path(settings.storage_dir) / "certificates" / str(job.id)
        out_dir.mkdir(parents=True, exist_ok=True)

        for row in rows:
            cert = Certificate(
                job_id=job.id,
                participant_id=row["participant_id"],
                participant_name=row["name"],
                email=row["email"],
                status="processing",
            )
            db.add(cert)
            db.commit()
            db.refresh(cert)

            try:
                path = out_dir / f"{row['participant_id']}.pdf"
                generate_certificate(template.filename, str(path), row)
                cert.status = "generated"
                cert.file_path = str(path)
                job.succeeded += 1
            except Exception as exc:
                logger.exception("Certificate generation failed for %s", row["participant_id"])
                cert.status = "failed"
                cert.error_message = str(exc)
                job.failed += 1
            finally:
                job.processed += 1
                db.commit()

        job.status = "completed" if job.failed == 0 else "completed_with_errors"
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:
        logger.exception("Generation job %s failed", job_id)
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()
        try:
            Path(csv_path).unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not remove source CSV %s", csv_path)
