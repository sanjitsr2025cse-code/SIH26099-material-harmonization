"""Composable orchestration for the Milestone 1 foundation."""
import pandas as pd
from app.pipeline.classification import classify
from app.pipeline.extraction import (
    ExtractionConfig,
    extract_attributes,
    validate_attributes,
)
from app.pipeline.models import PipelineResult
from app.pipeline.normalization import NormalizationConfig, normalize_frame
from app.pipeline.profiling import profile
from app.pipeline.validation import validate

class MaterialPipeline:
    def __init__(self, *, normalization: NormalizationConfig | None = None,
                 extraction: ExtractionConfig | None = None,
                 categories: dict[str, list[str]] | None = None,
                 required_fields: tuple[str, ...] = ("description",),
                 type_rules: dict[str, type | str] | None = None,
                 attribute_rules: dict[str, dict] | None = None):
        self.normalization = normalization or NormalizationConfig()
        self.extraction = extraction or ExtractionConfig()
        self.categories = categories or {}
        self.required_fields = required_fields
        self.type_rules = type_rules or {}
        self.attribute_rules = attribute_rules or {}

    def run(self, frame: pd.DataFrame) -> PipelineResult:
        validation = validate(frame, self.required_fields, self.type_rules)
        result = normalize_frame(frame, config=self.normalization) if "description" in frame else frame.copy()
        if "normalized_description" in result:
            result["extracted_attributes"] = result["normalized_description"].map(
                lambda x: extract_attributes(x, self.extraction))
            result["attribute_validation"] = result["extracted_attributes"].map(
                lambda x: validate_attributes(x, self.attribute_rules))
            result["material_category"] = result["normalized_description"].map(
                lambda x: classify(x, self.categories))
        return PipelineResult(result.to_dict(orient="records"), validation, profile(result), result)
