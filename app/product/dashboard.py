"""Optional Streamlit dashboard entry point.

Streamlit is imported only when ``run`` is called, so API and test imports do
not require the optional UI dependency.
"""
from typing import Any


def run(registry: Any = None) -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError(
            "The dashboard is optional; install Streamlit to run it."
        ) from exc
    from app.product.registry import MaterialRegistry
    registry = registry or MaterialRegistry()
    st.title("Material Harmonization Registry")
    uploaded = st.file_uploader("Upload material dataset", type=["csv", "xlsx", "xls"])
    if uploaded is not None:
        import pandas as pd
        frame = (
            pd.read_csv(uploaded)
            if uploaded.name.lower().endswith(".csv")
            else pd.read_excel(uploaded)
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
            registry.ingest(frame.to_dict("records"))
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
