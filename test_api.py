import time
from pathlib import Path


def wait_for_completion(client, job_id, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get(f"/api/v1/generation-jobs/{job_id}")
        data = response.json()
        if data["status"] in {"completed", "completed_with_errors", "failed"}:
            return data
        time.sleep(0.05)
    raise AssertionError("Job did not finish in time")


def test_create_generation_job(client):
    response = client.post("/api/v1/generation-jobs", json={"recipients": [
        {"name": "Amit Shah", "course_name": "Python Basics", "issue_date": "2026-10-07"}
    ]})
    assert response.status_code == 202
    assert response.json()["total"] == 1


def test_input_validation(client):
    response = client.post("/api/v1/generation-jobs", json={"recipients": [
        {"name": "", "course_name": "Python", "issue_date": "2026-10-07"}
    ]})
    assert response.status_code == 422


def test_certificate_generation(client):
    response = client.post("/api/v1/generation-jobs", json={"recipients": [
        {"name": "Amit Shah", "course_name": "Python Basics", "issue_date": "2026-10-07"}
    ]})
    job = wait_for_completion(client, response.json()["job_id"])
    assert job["successful"] == 1
    assert job["failed"] == 0
    assert job["progress_percent"] == 100


def test_job_status_progress(client):
    response = client.post("/api/v1/generation-jobs", json={"recipients": [
        {"name": "Amit Shah", "course_name": "Python Basics", "issue_date": "2026-10-07"},
        {"name": "Neha Patil", "course_name": "Python Basics", "issue_date": "2026-10-07"},
    ]})
    job_id = response.json()["job_id"]
    data = wait_for_completion(client, job_id)
    assert data["completed"] == 2
    assert data["progress_percent"] == 100
    assert len(data["certificates"]) == 2


def test_individual_certificate_failure_does_not_stop_job(client, monkeypatch):
    from app import main
    original = main.generate_certificate

    def flaky_generator(name, course_name, issue_date, certificate_id):
        if name == "Failure Person":
            raise RuntimeError("template rendering failed")
        return original(name, course_name, issue_date, certificate_id)

    monkeypatch.setattr(main, "generate_certificate", flaky_generator)
    response = client.post("/api/v1/generation-jobs", json={"recipients": [
        {"name": "Failure Person", "course_name": "Course", "issue_date": "2026-10-07"},
        {"name": "Successful Person", "course_name": "Course", "issue_date": "2026-10-07"},
    ]})
    data = wait_for_completion(client, response.json()["job_id"])
    assert data["status"] == "completed_with_errors"
    assert data["failed"] == 1
    assert data["successful"] == 1


def test_retrieve_generated_certificate(client):
    response = client.post("/api/v1/generation-jobs", json={"recipients": [
        {"name": "Amit Shah", "course_name": "Python Basics", "issue_date": "2026-10-07"}
    ]})
    data = wait_for_completion(client, response.json()["job_id"])
    certificate_id = data["certificates"][0]["id"]
    download = client.get(f"/api/v1/certificates/{certificate_id}")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")
