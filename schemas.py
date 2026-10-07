from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class Recipient(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    course_name: str = Field(min_length=2, max_length=300)
    issue_date: str = Field(min_length=1, max_length=50)

    @field_validator("name", "course_name", "issue_date")
    @classmethod
    def strip_values(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

class GenerationRequest(BaseModel):
    recipients: List[Recipient] = Field(min_length=1, max_length=10000)

class CertificateResult(BaseModel):
    id: int
    recipient_name: str
    status: str
    download_url: Optional[str] = None
    error: Optional[str] = None

class JobStatus(BaseModel):
    job_id: int
    status: str
    total: int
    successful: int
    failed: int
    completed: int
    progress_percent: float
    certificates: List[CertificateResult]
