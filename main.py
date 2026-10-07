from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .certificate import generate_certificate
from .database import Base, engine, get_db, SessionLocal
from .models import Certificate, GenerationJob
from .schemas import GenerationRequest, JobStatus

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Bulk Certificate Generator", version="1.0.0")
executor = ThreadPoolExecutor(max_workers=4)


def process_job(job_id: int):
    db = SessionLocal()
    try:
        job = db.get(GenerationJob, job_id)
        if not job:
            return
        job.status = "processing"
        db.commit()
        certs = db.query(Certificate).filter(Certificate.job_id == job_id).all()
        for cert in certs:
            try:
                cert.status = "processing"
                db.commit()
                cert.file_path = generate_certificate(cert.recipient_name, cert.course_name, cert.issue_date, cert.id)
                cert.status = "completed"
                job.successful += 1
            except Exception as exc:
                cert.status = "failed"
                cert.error_message = str(exc)
                job.failed += 1
            db.commit()
        job.status = "completed_with_errors" if job.failed else "completed"
        db.commit()
    except Exception:
        db.rollback()
        job = db.get(GenerationJob, job_id)
        if job:
            job.status = "failed"
            db.commit()
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/generation-jobs", status_code=202)
def create_generation_job(request: GenerationRequest, db: Session = Depends(get_db)):
    job = GenerationJob(total=len(request.recipients), status="queued")
    db.add(job)
    db.flush()
    for recipient in request.recipients:
        db.add(Certificate(job_id=job.id, recipient_name=recipient.name,
                           course_name=recipient.course_name, issue_date=recipient.issue_date))
    db.commit()
    executor.submit(process_job, job.id)
    return {"job_id": job.id, "status": "queued", "total": job.total,
            "status_url": f"/api/v1/generation-jobs/{job.id}"}

@app.get("/api/v1/generation-jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    certificates = []
    for cert in job.certificates:
        certificates.append({
            "id": cert.id,
            "recipient_name": cert.recipient_name,
            "status": cert.status,
            "download_url": f"/api/v1/certificates/{cert.id}" if cert.status == "completed" else None,
            "error": cert.error_message,
        })
    completed = job.successful + job.failed
    return JobStatus(job_id=job.id, status=job.status, total=job.total,
                     successful=job.successful, failed=job.failed, completed=completed,
                     progress_percent=round((completed / job.total) * 100, 2) if job.total else 100,
                     certificates=certificates)

@app.get("/api/v1/certificates/{certificate_id}")
def download_certificate(certificate_id: int, db: Session = Depends(get_db)):
    cert = db.get(Certificate, certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.status != "completed" or not cert.file_path:
        raise HTTPException(status_code=409, detail="Certificate is not available")
    path = Path(cert.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Certificate file not found")
    return FileResponse(path, media_type="application/pdf", filename=path.name)
