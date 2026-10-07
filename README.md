# Bulk Certificate Generator

A FastAPI backend that accepts a single bulk certificate-generation request, validates recipients, processes certificates in the background, tracks per-recipient status, and exposes generated PDF certificates for download.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- SQLite by default (PostgreSQL-compatible through `DATABASE_URL`)
- ReportLab for PDF generation
- Pytest + FastAPI TestClient

## Architecture / design decisions

### Why background processing?
Bulk PDF generation can take longer than a normal HTTP request. The API therefore creates the job and returns `202 Accepted` immediately. A worker pool processes certificates independently in the background.

### Why one database row per certificate?
The `generation_jobs` table stores aggregate progress, while `certificates` stores each recipient's status, output path, and error. This makes it possible to identify exactly which recipients succeeded or failed.

### Failure isolation
Each certificate is generated inside its own `try/except`. A failed recipient is marked `failed`, its error is stored, and processing continues for the remaining recipients.

### Template
The project intentionally uses one predefined ReportLab template in `app/certificate.py`. No template editor or multi-template system is included because it is outside the requirements.

### Production note
For a high-volume production deployment, replace the in-process `ThreadPoolExecutor` with a durable queue such as Celery/RQ + Redis and use object storage for generated PDFs. The API/database model can remain largely the same.

## Setup

```bash
python -m venv .venv
```

Windows:
```bash
.venv\\Scripts\\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Run

From the project root:

```bash
uvicorn app.main:app --reload
```

API docs:
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## Create a generation job

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/generation-jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": [
      {
        "name": "Amit Shah",
        "course_name": "Python Basics",
        "issue_date": "2026-10-07"
      },
      {
        "name": "Neha Patil",
        "course_name": "Python Basics",
        "issue_date": "2026-10-07"
      }
    ]
  }'
```

The API returns a job ID, for example:

```json
{
  "job_id": 1,
  "status": "queued",
  "total": 2,
  "status_url": "/api/v1/generation-jobs/1"
}
```

## Check status

```bash
curl "http://127.0.0.1:8000/api/v1/generation-jobs/1"
```

The response includes total, successful, failed, completion percentage, and individual certificate results.

## Retrieve a generated certificate

After a certificate has `status: completed`, use its download URL:

```bash
curl -L "http://127.0.0.1:8000/api/v1/certificates/1" -o certificate.pdf
```

## Run tests

```bash
pytest -q
```

The test suite covers:

- Creating a generation job
- Input validation
- Certificate generation
- Job progress/status
- Individual certificate failure isolation
- Certificate retrieval

## Project structure

```text
bulk-certificate-generator/
├── app/
│   ├── __init__.py
│   ├── certificate.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
├── generated/
├── templates/
├── tests/
│   ├── conftest.py
│   └── test_api.py
├── .gitignore
├── README.md
└── requirements.txt
```

## API summary

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/v1/generation-jobs` | Submit bulk generation |
| GET | `/api/v1/generation-jobs/{job_id}` | Track job/progress |
| GET | `/api/v1/certificates/{certificate_id}` | Download generated PDF |
