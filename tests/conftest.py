from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app, storage


@pytest.fixture
def client():
    """Return a test client with empty storage."""

    storage.clear()

    with TestClient(app) as test_client:
        yield test_client

    storage.clear()


@pytest.fixture
def sample_csv_bytes():
    """Return the sample CSV as bytes."""

    filepath = Path("fixtures") / "sample_data.csv"
    return filepath.read_bytes()


@pytest.fixture
def uploaded_dataset_id(client, sample_csv_bytes):
    """Upload the sample CSV and return its dataset ID."""

    response = client.post(
        "/upload",
        files={
            "file": (
                "sample_data.csv",
                sample_csv_bytes,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    return response.json()["id"]


@pytest.fixture
def processing_body():
    """Return the processing request configuration."""

    return {
        "validation": {
            "required_columns": [
                "student_id",
                "score",
            ],
            "numeric_columns": [
                "score",
            ],
        },
        "processing": {
            "remove_duplicates": True,
            "missing": {
                "enabled": True,
                "axis": "rows",
            },
            "outliers": {
                "enabled": False,
                "columns": [],
                "method": "iqr",
                "threshold": 1.5,
            },
        },
    }