# MP2 REST API

This project is a FastAPI application for uploading, storing, validating, processing, and retrieving CSV datasets. Uploaded datasets are stored in memory as pandas DataFrames. The API reuses the MP1 data pipeline to validate numeric and required columns, remove duplicates, handle missing values, and optionally remove outliers.

## API Endpoints

- `GET /health` checks whether the API is running.
- `POST /upload` uploads and stores a CSV dataset.
- `GET /datasets/{dataset_id}` retrieves records from a stored dataset.
- `POST /datasets/{dataset_id}/process` validates and processes a stored dataset.

Each response includes an `X-Request-ID` header, and the middleware logs the request method, path, status code, and duration.

## Run the Application

```bash
source venv/bin/activate
python -m uvicorn main:app --reload