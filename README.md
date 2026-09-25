# Bulk Certificate Generator

A Python/FastAPI backend for generating participant certificates in bulk from a certificate template and CSV participant data.

This version is intentionally **Docker-free for local development**: it uses SQLite for persistence and FastAPI `BackgroundTasks` for asynchronous certificate generation. No PostgreSQL, Redis, Celery, WSL, or Docker installation is required to run the project.

## Assignment requirements covered

- JWT authentication and authenticated resource ownership.
- Certificate template upload and validation.
- Bulk participant CSV upload and validation.
- Asynchronous/background certificate generation.
- Job lifecycle and progress tracking: `queued` → `processing` → `completed` / `completed_with_errors` / `failed`.
- Per-certificate success/failure status.
- Generated PDF download.
- Database persistence with SQLAlchemy.
- Failure isolation so one bad participant does not discard the entire batch.
- Batch-size validation for larger inputs.
- Automated tests for API and CSV validation.
- Sample template and participant data.
- OpenAPI/Swagger documentation through FastAPI.
- Clear assumptions, trade-offs, limitations, and future improvements.

## Architecture

```text
                 ┌──────────────────────┐
                 │       Client         │
                 │ Swagger / Postman    │
                 └──────────┬───────────┘
                            │ HTTP
                            ▼
                 ┌──────────────────────┐
                 │       FastAPI        │
                 │ Auth + validation    │
                 └──────────┬───────────┘
                            │
                ┌───────────┴────────────┐
                ▼                        ▼
        ┌───────────────┐       ┌─────────────────┐
        │    SQLite     │       │ BackgroundTasks │
        │ users/jobs/   │       │ certificate     │
        │ certificates  │       │ generation      │
        └───────────────┘       └────────┬────────┘
                                         │
                                         ▼
                               ┌──────────────────┐
                               │ Local file store │
                               │ templates + PDFs │
                               └──────────────────┘
```

### Request flow

1. User registers/logs in and receives a JWT.
2. Authenticated user uploads a PNG/JPEG certificate template.
3. User uploads a CSV and creates a generation job. The CSV is validated before the job is created.
4. The API persists the job and source CSV, then schedules the generation function as a FastAPI background task and immediately returns `202 Accepted`.
5. The background worker processes participants and updates job/certificate progress in SQLite.
6. The client polls `GET /jobs/{job_id}` until a terminal state is reached.
7. The client lists generated certificates and downloads individual PDFs.

## Why FastAPI + SQLite + BackgroundTasks?

- **FastAPI:** request validation, dependency injection, automatic OpenAPI documentation, and a clean Python API.
- **SQLite:** zero-configuration local database that makes the assignment immediately runnable on a Windows laptop without Docker or a separately installed database server.
- **BackgroundTasks:** keeps long-running certificate generation out of the request/response path while avoiding Redis/Celery infrastructure for a take-home assignment.
- **Local filesystem:** intentionally simple. Generated files and templates are stored under `storage/`.

The implementation deliberately avoids Kubernetes, Kafka, Redis, Celery, and a separate frontend because those technologies are not necessary to demonstrate the core backend design and would make local evaluation substantially harder.

### Production trade-off

FastAPI `BackgroundTasks` is an in-process background mechanism. A process crash/restart can interrupt a running job. For a production deployment, the background layer should be replaced with a durable queue such as Celery/RQ/SQS and Redis/RabbitMQ/SQS-backed delivery, together with a transactional outbox or another durable handoff. The API/data model is intentionally kept compatible with that evolution.

## Data model

### `users`
`id`, `email`, `password_hash`, `role`, `created_at`

### `templates`
`id`, `name`, `filename`, `content_type`, `created_by`, `created_at`

### `generation_jobs`
`id`, `template_id`, `created_by`, `status`, `total`, `processed`, `succeeded`, `failed`, `error_message`, timestamps

### `certificates`
`id`, `job_id`, `participant_id`, `participant_name`, `email`, `status`, `file_path`, `error_message`, `created_at`

## API

### Authentication

- `POST /auth/register`
- `POST /auth/login`

### Templates

- `POST /templates` — multipart form: `name`, `file`

### Generation jobs

- `POST /jobs` — multipart form: `template_id`, `participants`
- `GET /jobs/{job_id}` — status/progress
- `GET /jobs/{job_id}/certificates` — generated/failed certificate records
- `GET /jobs/{job_id}/certificates/{certificate_id}/download` — PDF download

### Health

- `GET /health`

Interactive API docs:

`http://127.0.0.1:8000/docs`

## CSV contract

Required headers:

```csv
participant_id,name,email
P001,Aarav Sharma,aarav@example.com
```

The API rejects missing required columns, missing required values, empty batches, invalid UTF-8, and batches larger than `MAX_BATCH_SIZE`.

## Windows setup — no Docker required

### Prerequisites

- Python 3.11+ recommended.
- Git (only needed if cloning the repository).
- No Docker, WSL, PostgreSQL, Redis, or Celery installation is required.

### Option A — one command

Open PowerShell in the repository folder and run:

```powershell
.\run.ps1
```

The script creates `.venv`, installs dependencies, creates `.env`, and starts Uvicorn.

If PowerShell blocks local scripts, use Option B below instead.

### Option B — manual setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

If `Copy-Item` says `.env` already exists, that's fine.

Open:

`http://127.0.0.1:8000/docs`

## Demo sequence

1. Register a user.
2. Login and obtain the JWT.
3. Click **Authorize** in Swagger and provide the bearer token.
4. Upload `samples/certificate_template.png` through `POST /templates`.
5. Upload `samples/participants.csv` through `POST /jobs` with the returned template ID.
6. The API immediately returns a job with status `queued`/`processing`.
7. Poll `GET /jobs/{job_id}` and observe `processed`, `succeeded`, and `failed` counters.
8. When complete, call `GET /jobs/{job_id}/certificates`.
9. Download a generated PDF from the returned download endpoint.

### Example registration

```powershell
curl.exe -X POST http://127.0.0.1:8000/auth/register `
  -H "Content-Type: application/json" `
  -d '{"email":"demo@example.com","password":"StrongPass123!"}'
```

### Example login

```powershell
curl.exe -X POST http://127.0.0.1:8000/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email":"demo@example.com","password":"StrongPass123!"}'
```

For the rest of the demo, Swagger is recommended because multipart file uploads and bearer authorization are easier to use there.

## Testing

Activate the virtual environment first:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then:

```powershell
pytest -q
```

The test suite covers health/authentication smoke paths and CSV validation. A larger production suite should additionally cover worker recovery, authorization boundaries, malformed images, download security, and end-to-end generation.

## Failure handling and consistency

- Invalid CSV data is rejected before a job is created.
- A job is persisted before background processing starts.
- Each certificate has an independent status/error, so one bad participant does not discard the whole batch.
- Unexpected job-level exceptions mark the job as `failed`.
- Partial participant failures result in `completed_with_errors` while successful certificates remain downloadable.
- Job ownership is checked for status, listing, and download operations.

## Performance considerations

- The HTTP request does not synchronously generate all PDFs.
- The worker reads the stored CSV rather than keeping the upload request open.
- Batch size is configurable.
- Certificate generation can be moved to a durable queue and horizontally scaled in production.
- SQLite is suitable for a local take-home demo, not a high-concurrency production workload.

For very large workloads, production improvements would include chunked CSV processing, bulk database operations, object storage, and multiple durable workers.

## Security considerations

- Passwords are bcrypt-hashed; plaintext passwords are not stored.
- JWTs expire.
- Protected resources require authentication.
- Users can only access their own jobs/certificates.
- Uploaded templates are limited to PNG/JPEG and validated as actual images.
- Production deployment should use HTTPS, a strong secret from a secret manager, object-storage signed URLs, rate limiting, malware scanning, and stricter upload/path controls.

## Assumptions

1. The template is a PNG/JPEG background and participant name/certificate ID are overlaid at fixed coordinates.
2. Each participant row represents one certificate.
3. Participant email is stored for future delivery integrations; email sending is out of scope.
4. A certificate is generated when its PDF is successfully written.
5. Local storage is acceptable for the take-home demo.
6. The authenticated user who creates a job owns the resulting certificates.

## Known limitations

- Template positioning is fixed rather than user-configurable.
- Local filesystem storage is not suitable for multi-host production deployments.
- No email delivery is implemented.
- No admin UI is included.
- In-process background tasks are not durable across process crashes/restarts.
- Polling is used for job progress; WebSockets/SSE are intentionally omitted.
- The sample implementation generates PDFs serially within a background task.

## Future improvements

- PostgreSQL + Alembic migrations for production persistence.
- Redis/RabbitMQ/SQS + Celery/RQ for durable background processing.
- S3-compatible object storage with signed download URLs.
- Configurable template placeholders and a template editor.
- Chunked jobs and controlled worker concurrency.
- Transactional outbox/event delivery.
- Idempotency keys and duplicate participant detection.
- SSE/WebSocket progress updates.
- Admin/audit dashboard and role-based permissions.
- Prometheus metrics, structured logging, tracing, and alerting.
- Virus scanning and stronger upload/content-disposition hardening.

## Repository structure

```text
bulk-certificate-generator/
├── app/
│   ├── api/                 # HTTP routes
│   ├── core/                # settings and security dependencies
│   ├── db/                  # SQLAlchemy engine/session
│   ├── models/              # database models
│   ├── schemas/             # request/response schemas
│   ├── services/            # CSV and PDF generation logic
│   ├── tasks/               # background job implementation
│   └── main.py              # FastAPI application
├── samples/
│   ├── certificate_template.png
│   └── participants.csv
├── tests/
├── .env.example
├── requirements.txt
├── run.ps1                  # Windows one-command launcher
├── run.bat                  # Windows CMD launcher
├── Dockerfile               # optional production/container packaging
├── docker-compose.yml       # optional container deployment
├── Makefile
└── README.md
```

## AI usage disclosure

AI tools were used during development to assist with architecture brainstorming, implementation scaffolding, documentation, and test-case suggestions. The submitted design and code should be reviewed and understood by the author before submission; AI output was treated as development assistance rather than a substitute for engineering judgment.

## Submission checklist

- [x] Complete Python backend source code
- [x] FastAPI framework
- [x] Authentication/authorization
- [x] Template upload and validation
- [x] Bulk participant CSV upload and validation
- [x] Background/asynchronous processing
- [x] Generation status/progress
- [x] PDF certificate output
- [x] Failure handling and per-certificate status
- [x] Database persistence
- [x] Tests
- [x] Sample template and participant CSV
- [x] Setup instructions
- [x] Architecture overview
- [x] Assumptions and trade-offs
- [x] Known limitations
- [x] Future improvements
- [x] AI disclosure
