from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for the health endpoint."""

    status: str
    version: str


class DatasetInfo(BaseModel):
    """Metadata for a stored dataset."""

    id: int
    filename: str
    rows: int
    columns: int
    column_names: list[str]


class ValidationSettings(BaseModel):
    """Settings used when validating a dataset."""

    required_columns: list[str] = Field(default_factory=list)
    numeric_columns: list[str] = Field(default_factory=list)


class MissingSettings(BaseModel):
    """Settings for handling missing values."""

    enabled: bool = True
    axis: str = "rows"


class OutlierSettings(BaseModel):
    """Settings for removing outliers."""

    enabled: bool = False
    columns: list[str] = Field(default_factory=list)
    method: str = "iqr"
    threshold: float = 1.5


class ProcessingSettings(BaseModel):
    """Settings for cleaning a dataset."""

    remove_duplicates: bool = True
    missing: MissingSettings = Field(default_factory=MissingSettings)
    outliers: OutlierSettings = Field(default_factory=OutlierSettings)


class ProcessConfig(BaseModel):
    """Complete validation and processing configuration."""

    validation: ValidationSettings = Field(
        default_factory=ValidationSettings
    )
    processing: ProcessingSettings = Field(
        default_factory=ProcessingSettings
    )


class ProcessingReport(BaseModel):
    """Summary returned after processing a dataset."""

    id: int
    validation_rows_removed: int
    cleaning_report: dict[str, int]