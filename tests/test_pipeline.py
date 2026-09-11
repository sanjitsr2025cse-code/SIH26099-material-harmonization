import io
import pandas as pd

from app.pipeline.extraction import ExtractionConfig, extract_attributes, validate_attributes
from app.pipeline.ingestion import ingest
from app.pipeline.normalization import NormalizationConfig, normalize_text
from app.pipeline.pipeline import MaterialPipeline
from app.pipeline.profiling import profile
from app.pipeline.validation import validate

def test_csv_ingestion_preserves_description():
    frame = ingest(io.StringIO("description,code\nSteel bolt,A1\n"), source_name="x.csv")
    assert frame.loc[0, "original_description"] == "Steel bolt"

def test_pipeline_preserves_description_and_validates_types_and_attributes():
    result = MaterialPipeline(
        normalization=NormalizationConfig(units={"mm": "millimeter"}),
        type_rules={"quantity": int},
        extraction=ExtractionConfig(
            patterns={"size": r"(?P<value>\d+)\s+(?P<unit>millimeter)"}
        ),
        attribute_rules={"size": {"unit": "millimeter"}},
    ).run(pd.DataFrame({"description": ["10 mm bolt"], "quantity": [1]}))

    record = result.records[0]
    assert record["original_description"] == "10 mm bolt"
    assert record["attribute_validation"]["valid"] is True
    assert result.validation.valid is True

def test_validation_and_profile_report_bad_and_duplicate_rows():
    frame = pd.DataFrame({"description": ["bolt", "", "bolt"], "code": [1, 2, 1]})
    result = validate(frame)
    assert not result.valid
    assert any(error["code"] == "missing_value" for error in result.errors)
    assert profile(frame).duplicate_rows == 1

def test_configurable_normalization_extraction_and_classification():
    text = normalize_text("  SS bolt, 10 MM ", NormalizationConfig(
        strip_punctuation=True, units={"mm": "millimeter"}, abbreviations={"ss": "stainless steel"}))
    assert text == "stainless steel bolt 10 millimeter"
    attrs = extract_attributes(text, ExtractionConfig(
        patterns={"size": r"(?P<value>\d+)\s+(?P<unit>millimeter)"}))
    assert attrs["size"]["value"] == "10"
    assert validate_attributes(attrs, {"size": {"unit": "millimeter"}})["valid"]
    result = MaterialPipeline(categories={"fastener": ["bolt"]}).run(
        pd.DataFrame({"description": ["SS bolt"]}))
    assert result.records[0]["material_category"] == "fastener"
