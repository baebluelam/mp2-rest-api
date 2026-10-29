def test_upload_csv(client, sample_csv_bytes):
    """A valid CSV should be uploaded and stored."""

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

    body = response.json()

    assert body["rows"] == 6
    assert body["columns"] == 2
    assert isinstance(body["id"], int)
    assert body["id"] > 0


def test_process_and_retrieve(
    client,
    uploaded_dataset_id,
    processing_body,
):
    """A dataset should be validated, cleaned, and updated."""

    process_response = client.post(
        f"/datasets/{uploaded_dataset_id}/process",
        json=processing_body,
    )

    assert process_response.status_code == 200

    report = process_response.json()

    assert report["validation_rows_removed"] == 1
    assert report["cleaning_report"]["rows_before"] == 5
    assert report["cleaning_report"]["rows_after"] == 3
    assert report["cleaning_report"]["rows_removed"] == 2

    retrieve_response = client.get(
        f"/datasets/{uploaded_dataset_id}"
    )

    assert retrieve_response.status_code == 200

    retrieved = retrieve_response.json()

    assert retrieved["total_rows"] == 3

    expected_records = [
        {
            "student_id": 1,
            "score": 80,
        },
        {
            "student_id": 2,
            "score": 90,
        },
        {
            "student_id": 5,
            "score": 85,
        },
    ]

    assert retrieved["data"] == expected_records


def test_retrieve_missing_dataset(client):
    """Retrieving an unknown dataset should return 404."""

    response = client.get("/datasets/999")

    assert response.status_code == 404