import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TEST_DB = "/tmp/bulk_certificates_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from app.database import Base, engine
from app.main import app

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
