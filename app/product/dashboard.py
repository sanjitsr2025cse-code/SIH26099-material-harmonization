"""Optional Streamlit dashboard entry point.

Streamlit is imported only when ``run`` is called, so API and test imports do
not require the optional UI dependency.
"""
import ast
import json
import math
from typing import Any


def parse_attributes(value: Any) -> dict[str, Any]:
    """Normalize dashboard-uploaded attribute values to dictionaries."""
    if isinstance(value, dict):
        return value
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return {}
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return {}
    return parsed if isinstance(parsed, dict) else {}


def prepare_dashboard_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prepare uploaded records without changing existing non-string values."""
    prepared = []
    for record in records:
        value = dict(record)
        if "attributes" in value:
            value["attributes"] = parse_attributes(value["attributes"])
        prepared.append(value)
    return prepared


def ingest_dashboard_records(registry: Any, records: list[dict[str, Any]]) -> Any:
    """Normalize uploaded records and ingest them into the supplied registry."""
    registry.ingest(prepare_dashboard_records(records))
    return registry


def demo_dataset_csv(size: int = 100, seed: int = 10_000) -> bytes:
    """Return a reproducible demo CSV using the shared synthetic dataset."""
    if size < 1:
        raise ValueError("size must be positive")
    import io
    import pandas as pd

    from app.benchmark.dataset import generate_dataset

    frame = pd.DataFrame(generate_dataset(size=size, seed=seed))
    output = io.StringIO()
    frame.to_csv(output, index=False)
    return output.getvalue().encode("utf-8")


def run(registry: Any = None) -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError(
            "The dashboard is optional; install Streamlit to run it."
        ) from exc
    from app.product.registry import MaterialRegistry
    if registry is None:
        registry = st.session_state.setdefault("material_registry", MaterialRegistry())
    st.title("Material Harmonization Registry")
    st.subheader("Demo dataset")
    demo_size = st.number_input(
        "Demo record count", min_value=1, max_value=10_000, value=100, step=1
    )
    if st.button("Generate Demo Dataset"):
        st.session_state["demo_dataset_csv"] = demo_dataset_csv(int(demo_size))
    generated_csv = st.session_state.get("demo_dataset_csv")
    if generated_csv:
        st.download_button(
            "Download Demo Dataset CSV",
            generated_csv,
            file_name="material_harmonization_demo.csv",
            mime="text/csv",
        )
        use_generated = st.checkbox("Use generated demo dataset", value=False)
    else:
        use_generated = False
    uploaded = st.file_uploader("Upload material dataset", type=["csv", "xlsx", "xls"])
    dataset = generated_csv if use_generated else uploaded
    if dataset is not None:
        import pandas as pd
        import io

        if isinstance(dataset, bytes):
            dataset = io.BytesIO(dataset)
            dataset.name = "material_harmonization_demo.csv"
        frame = (
            pd.read_csv(dataset)
            if dataset.name.lower().endswith(".csv")
            else pd.read_excel(dataset)
        )
        st.subheader("Validation results")
        st.write({"rows": len(frame), "columns": list(frame.columns)})
        if "description" not in frame.columns:
            st.error("Required column 'description' is missing.")
        else:
            empty_descriptions = int(frame["description"].isna().sum())
            duplicates = int(frame.duplicated().sum())
            st.json({
                "missing_descriptions": empty_descriptions,
                "duplicate_rows": duplicates,
                "valid": empty_descriptions == 0,
            })
            ingest_dashboard_records(registry, frame.to_dict("records"))
            st.success(f"Loaded {len(registry.records)} records")
    query = st.text_input("Search canonical materials")
    if query:
        st.write([material.record for material in registry.search(query)])
    st.subheader("Canonical CNMC records")
    st.write([
        {"cnmc_id": material.cnmc_id, "members": material.member_ids,
         "record": material.record}
        for material in registry.list_canonicals()
    ])
    st.subheader("Review candidates")
    for item in registry.candidates():
        with st.expander(f"{item.review_id}: {item.ai_decision.decision}"):
            st.write({
                "left_id": item.left_id,
                "right_id": item.right_id,
                "confidence": item.ai_decision.confidence,
                "explanation": item.ai_decision.explanation,
            })
            action = st.selectbox(
                "Decision",
                ["APPROVE", "REJECT", "OVERRIDE"],
                key=f"action-{item.review_id}",
            )
            target_cnmc = None
            if action == "OVERRIDE":
                cnmc_ids = [material.cnmc_id for material in registry.list_canonicals()]
                if cnmc_ids:
                    target_cnmc = st.selectbox(
                        "Target canonical material",
                        cnmc_ids,
                        key=f"target-{item.review_id}",
                    )
            reviewer = st.text_input("Reviewer", key=f"reviewer-{item.review_id}")
            explanation = st.text_input("Explanation", key=f"explanation-{item.review_id}")
            if st.button("Save decision", key=f"save-{item.review_id}"):
                if not reviewer.strip():
                    st.error("Reviewer is required.")
                else:
                    registry.decide_review(
                        item.review_id, action, reviewer.strip(), explanation, target_cnmc
                    )
                    st.success("Review decision saved.")
    st.subheader("Statistics")
    st.json(registry.statistics())


if __name__ == "__main__":
    run()
