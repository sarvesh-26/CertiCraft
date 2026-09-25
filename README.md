# Bulk Certificate Generator

A Python/FastAPI backend that lets an organization generate certificates for many participants at once.

The basic flow is:

1. Upload a certificate template.
2. Upload participant details as a CSV.
3. Create a certificate generation job.
4. The certificates are generated in the background.
5. Check the job progress.
6. Download the generated certificates.

I built this as a backend-focused take-home assignment, keeping the setup simple so it can be run locally without Docker.

---

## Tech Stack

- Python 3.11+
- FastAPI
- SQLite
- SQLAlchemy
- JWT authentication
- BackgroundTasks
- Pillow
- ReportLab
- Pytest

For local development, the project does **not** require Docker, PostgreSQL, Redis, Celery, or WSL.

---

## How it works

The application has three main parts:

```text
                Client / Swagger
                       |
                       v
                 FastAPI API
                  /       \
                 /         \
                v           v
           SQLite DB    Background Task
                            |
                            v
                    Certificate Generator
                            |
                            v
                       PDF Files
```
Request flow
1. A user registers and logs in.
2. The API returns a JWT token.
3. The user uploads a certificate template.
4. The user uploads participant information as a CSV.
5. A generation job is created.
6. The API returns the job ID immediately instead of making the user wait for all certificates.
7. Certificate generation runs in the background.
8. The job keeps track of how many certificates succeeded or failed.
9. Once the job is complete, the generated certificates can be listed and downloaded.
Main Features
Authentication
- User registration
- Login with email and password
- JWT-based authentication
- Protected APIs
- Users can only access their own jobs and certificates
Certificate Templates
- Upload PNG/JPEG certificate templates
- Validate uploaded files
- Store templates locally
Bulk Generation
- Upload participant data using CSV
- Validate the CSV before creating a job
- Generate certificates in the background
- Track progress while the job is running
- Continue processing even if one participant fails
Certificate Output
- Generate PDF certificates
- Track individual certificate status
- Download completed certificates
API Endpoints
Authentication
POST /auth/register
POST /auth/login

Templates
POST /templates

Upload a certificate template.
Jobs
POST /jobs
GET  /jobs/{job_id}
GET  /jobs/{job_id}/certificates
GET  /jobs/{job_id}/certificates/{certificate_id}/download

Health
GET /health

Running the Project
Requirements
You only need:
- Python 3.11+
- Git (if cloning the repository)
You do not need:
- Docker
- PostgreSQL
- Redis
- Celery
- WSL
Option 1: Run using the PowerShell script
Open PowerShell in the project folder:
.\run.ps1

This will:
- Create the virtual environment
- Install the required packages
- Create the .env file
- Start the FastAPI application
If PowerShell doesn't allow the script to run, use Option 2.
Option 2: Run manually
Create a virtual environment:
py -m venv .venv

Activate it:
.\.venv\Scripts\Activate.ps1

Install dependencies:
python -m pip install --upgrade pip
pip install -r requirements.txt

Create the environment file:
Copy-Item .env.example .env

Start the application:
uvicorn app.main:app --reload

The API will be available at:
http://127.0.0.1:8000

Swagger documentation:
http://127.0.0.1:8000/docs

Running the Demo
The easiest way to test the application is through Swagger.
1. Register
Use:
POST /auth/register

Example:
{
  "email": "demo@example.com",
  "password": "StrongPass123!"
}

2. Login
Use:
POST /auth/login

Copy the returned JWT token.
3. Authorize Swagger
Click the Authorize button at the top of Swagger and enter the token.
4. Upload the certificate template
Use:
POST /templates

Sample template:
samples/certificate_template.png

Save the template ID returned by the API.
5. Create a generation job
Use:
POST /jobs

Upload:
samples/participants.csv

and provide the template ID.
The API returns a job ID and does not wait for all certificates to finish.
For example:
{
  "id": 1,
  "status": "queued",
  "total": 5,
  "processed": 0,
  "succeeded": 0,
  "failed": 0
}

6. Check the job
Use:
GET /jobs/{job_id}

You can keep checking this endpoint to see the progress.
Possible job states are:
queued
processing
completed
completed_with_errors
failed

7. View generated certificates
Use:
GET /jobs/{job_id}/certificates

8. Download a certificate
Use:
GET /jobs/{job_id}/certificates/{certificate_id}/download

CSV Format
The sample CSV is available at:
samples/participants.csv

The required columns are:
participant_id,name,email
P001,Aarav Sharma,aarav@example.com
P002,Ananya Rao,ananya@example.com

The API checks for:
- Required columns
- Required values
- Valid UTF-8 CSV
- Empty files/batches
- Maximum batch size
Why I chose this approach
FastAPI
I chose FastAPI because it provides:
- Simple API development
- Request validation
- Dependency injection
- JWT authentication support
- Automatic Swagger/OpenAPI documentation
- Good performance for this type of backend
SQLite
For this assignment, I wanted the project to be easy for someone else to run.
SQLite means there is no need to install or configure a separate database server.
For a production application, I would move this to PostgreSQL.
BackgroundTasks
Certificate generation can take time when there are many participants.
Instead of keeping the HTTP request open until every certificate is finished, the API creates a job and starts the generation in the background.
This allows the API to return quickly with a job ID.
For a production system with multiple workers and higher reliability requirements, I would use a proper task queue such as Celery/RQ with Redis, RabbitMQ, or a cloud queue.
Local file storage
Templates and generated PDFs are stored locally under:
storage/

This keeps the assignment simple.
For production, I would use something like S3 or another object-storage service.
Handling Failures
I tried to keep failures isolated.
For example, if one participant has bad data or their certificate cannot be generated, the entire batch should not have to fail.
Each certificate has its own status and error information.
A job can therefore finish as:
completed

or:
completed_with_errors

depending on what happened during processing.
Unexpected job-level errors result in:
failed

Database
The main tables are:
Users
Stores:
- User ID
- Email
- Password hash
- Role
- Created date
Templates
Stores:
- Template ID
- Name
- File information
- Owner
- Created date
Generation Jobs
Stores:
- Job ID
- Template
- Owner
- Status
- Total participants
- Processed count
- Successful count
- Failed count
- Error information
Certificates
Stores:
- Certificate ID
- Job ID
- Participant information
- Status
- Generated file path
- Error information
Testing
Run:
pytest -q

The tests cover the main API/authentication flow and CSV validation.
For a production system, I would add more tests around:
- Authorization boundaries
- Background worker failures
- Large CSV files
- Invalid images
- File download security
- Full end-to-end generation
Important Assumptions
A few assumptions were made because the assignment leaves some implementation details open:
1. The certificate template is a PNG/JPEG image.
2. Participant information is provided as CSV.
3. Each participant row represents one certificate.
4. Participant email is stored for possible future email delivery.
5. Email sending itself is outside the scope of this assignment.
6. The authenticated user who creates a job owns its certificates.
7. Local file storage is acceptable for the take-home assignment.
Known Limitations
There are a few things I would improve for a production version:
- Certificate text positioning is currently fixed.
- Files are stored locally.
- SQLite is intended for local/demo use.
- Background tasks are not durable if the application crashes.
- There is no email delivery.
- There is no admin dashboard.
- Job progress currently uses polling.
- Certificate generation is processed serially.
What I Would Improve for Production
If this system had to support much larger workloads, I would consider:
- PostgreSQL instead of SQLite
- Celery/RQ or a cloud queue for background jobs
- Redis/RabbitMQ/SQS
- S3-compatible object storage
- Multiple certificate workers
- Chunked CSV processing
- Idempotency keys
- Duplicate participant detection
- SSE/WebSockets for real-time progress
- Better monitoring and logging
- Prometheus metrics
- Distributed tracing
- Admin/audit dashboard
- Virus scanning for uploaded files
I intentionally didn't add all of these to the assignment because I wanted to keep the solution simple and focused on the core requirements.
Project Structure

```text 
bulk-certificate-generator/
│
├── app/
│   ├── api/              # API routes
│   ├── core/             # Settings and security
│   ├── db/               # Database setup
│   ├── models/           # Database models
│   ├── schemas/          # Request/response schemas
│   ├── services/         # CSV and certificate generation
│   ├── tasks/            # Background processing
│   └── main.py           # FastAPI application
│
├── samples/
│   ├── certificate_template.png
│   └── participants.csv
│
├── tests/
│
├── .env.example
├── .gitignore
├── requirements.txt
├── run.ps1
├── run.bat
├── README.md
└── ...

```
AI Usage
AI tools were used during development for:
- Brainstorming the architecture
- Getting implementation ideas
- Debugging issues
- Writing some initial code
- Improving documentation
- Suggesting test cases
I reviewed and tested the implementation myself and used AI as a development aid rather than as a replacement for understanding the code.


Author
Built as a backend engineering take-home assignment.

### Why I prefer this version

The original is technically solid, but phrases like **“transactional outbox,” “durable handoff,” “horizontally scaled,”** etc. make it sound more like something generated for a system-design document than a developer explaining their own take-home project. The revised version keeps those ideas where they matter, but explains them in plain language. The original architecture and trade-offs are still preserved. :chatgpt-content-reference{index="1"}

**I would use this version for your GitHub README.** It will be easier for the reviewer to scan and, more importantly, easier for **you to explain during the interview**.
