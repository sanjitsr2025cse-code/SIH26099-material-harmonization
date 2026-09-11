"""CSV and Excel ingestion with source text preservation."""
from pathlib import Path
from typing import IO
import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

def ingest(source: str | Path | IO[bytes] | IO[str], *, source_name: str | None = None,
           csv_kwargs: dict | None = None, excel_kwargs: dict | None = None) -> pd.DataFrame:
    """Read a tabular source and retain the exact description in original_description."""
    name = source_name or (str(source) if isinstance(source, (str, Path)) else "")
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported input format; use CSV or Excel (.xlsx/.xls)")
    if suffix == ".csv":
        frame = pd.read_csv(source, **(csv_kwargs or {}))
    else:
        frame = pd.read_excel(source, **(excel_kwargs or {}))
    if "description" in frame.columns and "original_description" not in frame.columns:
        frame["original_description"] = frame["description"]
    elif "material_description" in frame.columns and "original_description" not in frame.columns:
        frame["original_description"] = frame["material_description"]
    return frame

def ingest_file(path: str | Path, **kwargs) -> pd.DataFrame:
    return ingest(path, **kwargs)
