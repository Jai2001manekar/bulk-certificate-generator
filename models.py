from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from .database import Base

class GenerationJob(Base):
    __tablename__ = "generation_jobs"
    id = Column(Integer, primary_key=True)
    status = Column(String(30), nullable=False, default="queued")
    total = Column(Integer, nullable=False)
    successful = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    certificates = relationship("Certificate", back_populates="job", cascade="all, delete-orphan")

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("generation_jobs.id"), nullable=False)
    recipient_name = Column(String(200), nullable=False)
    course_name = Column(String(300), nullable=False)
    issue_date = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False, default="queued")
    file_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    job = relationship("GenerationJob", back_populates="certificates")
