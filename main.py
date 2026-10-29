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

from data_pipeline import (
    create_cleaning_report,
    process_data,
    validate_dataframe,
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

@app.post(
    "/datasets/{dataset_id}/process",
    response_model=ProcessingReport,
)
def process_dataset(dataset_id: int, config: ProcessConfig):
    """Validate and process a stored dataset using MP1 functions."""

    dataframe = storage.get(dataset_id)

    if dataframe is None:
        logger.warning("Dataset not found: %s", dataset_id)
        raise HTTPException(
            status_code=404,
            detail="Dataset not found",
        )

    config_dict = config.model_dump()
    validation_config = config_dict["validation"]
    numeric_columns = validation_config["numeric_columns"]

    missing_numeric_columns = [
        column
        for column in numeric_columns
        if column not in dataframe.columns
    ]

    if missing_numeric_columns:
        missing_names = ", ".join(missing_numeric_columns)
        raise HTTPException(
            status_code=400,
            detail=f"Numeric column not found: {missing_names}",
        )

    try:
        validated_dataframe = validate_dataframe(
            dataframe,
            validation_config["required_columns"],
            numeric_columns,
        )

        validation_rows_removed = (
            len(dataframe) - len(validated_dataframe)
        )

        validated_before_processing = validated_dataframe.copy()

        processed_dataframe = process_data(
            validated_dataframe,
            config_dict,
        )

        cleaning_report = create_cleaning_report(
            validated_before_processing,
            processed_dataframe,
        )

    except ValueError as error:
        logger.warning(
            "Processing failed for dataset %s: %s",
            dataset_id,
            error,
        )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    storage.update(dataset_id, processed_dataframe)

    logger.info(
        "Processed dataset: id=%s, validation_removed=%s, "
        "rows_before=%s, rows_after=%s",
        dataset_id,
        validation_rows_removed,
        cleaning_report["rows_before"],
        cleaning_report["rows_after"],
    )

    return {
        "id": dataset_id,
        "validation_rows_removed": validation_rows_removed,
        "cleaning_report": cleaning_report,
    }