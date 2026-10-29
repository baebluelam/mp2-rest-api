import io
import json
import logging
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from src import (
    DatasetInfo,
    DatasetStorage,
    HealthResponse,
    ProcessConfig,
    ProcessingReport,
    log_requests,
    setup_logging,
)


setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Data Processing API",
    version="1.0.0"
)
app.middleware("http")(log_requests)

storage = DatasetStorage()


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""

    return HealthResponse(
        status="ok",
        version="1.0.0"
    )


@app.post("/upload", response_model=DatasetInfo)
async def upload_dataset(file: UploadFile = File(...)):
    """Read and store a CSV upload."""

    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension != ".csv":
        logger.warning(
            f"Unsupported file format: {extension}"
        )

        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported"
        )

    try:
        contents = await file.read()
        dataframe = pd.read_csv(
            io.BytesIO(contents)
        )

    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError
    ) as error:
        logger.warning(
            f"Unable to read CSV file: {error}"
        )

        raise HTTPException(
            status_code=400,
            detail="The uploaded CSV file could not be read"
        ) from error

    dataset_id = storage.save(
        dataframe,
        filename
    )

    metadata = storage.get_metadata(dataset_id)

    logger.info(
        f"Uploaded dataset: id={dataset_id}, "
        f"filename={filename}, rows={len(dataframe)}"
    )

    return DatasetInfo(**metadata)


@app.get("/datasets/{dataset_id}")
def get_dataset(
    dataset_id: int,
    limit: int = Query(default=100, ge=1)
):
    """Return up to limit rows from a stored dataset."""

    dataframe = storage.get(dataset_id)

    if dataframe is None:
        logger.warning(
            f"Dataset not found: {dataset_id}"
        )

        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )

    records = json.loads(
        dataframe.head(limit).to_json(
            orient="records"
        )
    )

    logger.info(
        f"Retrieved dataset: id={dataset_id}, "
        f"returned_rows={len(records)}"
    )

    return {
        "id": dataset_id,
        "data": records,
        "total_rows": len(dataframe)
    }