"""Basic, dependency-light dataframe profiling."""
import pandas as pd
import json
from app.pipeline.models import ProfileResult

def profile(frame: pd.DataFrame) -> ProfileResult:
    columns = {}
    for name in frame.columns:
        series = frame[name]
        try:
            unique = int(series.nunique(dropna=True))
        except TypeError:
            # Extracted attributes are intentionally structured dictionaries.
            unique = int(series.dropna().map(lambda value: json.dumps(value, sort_keys=True, default=str)).nunique())
        columns[name] = {"dtype": str(series.dtype), "non_null": int(series.notna().sum()),
                         "unique": unique}
    try:
        duplicate_rows = int(frame.duplicated().sum())
    except TypeError:
        comparable = frame.map(lambda value: json.dumps(value, sort_keys=True, default=str)
                               if isinstance(value, (dict, list, set)) else value)
        duplicate_rows = int(comparable.duplicated().sum())
    return ProfileResult(len(frame), len(frame.columns), columns,
                         duplicate_rows,
                         {str(k): int(v) for k, v in frame.isna().sum().items()})
