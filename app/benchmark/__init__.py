"""Offline validation assets for the 10K material harmonization milestone."""

from .dataset import demo_dataset_csv, generate_dataset, generate_synthetic_dataset

try:
    from .runner import BenchmarkResult, run_10k_benchmark, run_benchmark
except ModuleNotFoundError as exc:
    if exc.name != "pandas":
        raise
    BenchmarkResult = None
    run_benchmark = None
    run_10k_benchmark = None

__all__ = [
    "BenchmarkResult", "demo_dataset_csv", "generate_dataset", "generate_synthetic_dataset",
    "run_benchmark", "run_10k_benchmark",
]
