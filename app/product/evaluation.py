"""Metrics for evaluating deterministic match decisions against labels."""
from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class EvaluationMetrics:
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float

    # Convenient names used by reporting clients.
    @property
    def tp(self) -> int: return self.true_positives
    @property
    def fp(self) -> int: return self.false_positives
    @property
    def fn(self) -> int: return self.false_negatives


def evaluate_decisions(
    decisions: Iterable[object],
    labels: Mapping[tuple[str, str], bool] | None = None,
) -> EvaluationMetrics:
    """Evaluate decisions, where labels map an ID pair to equivalence.

    A decision is accepted as positive only for ``EQUIVALENT``.  Objects may
    be ``AIDecision`` instances or dictionaries, keeping CSV/UI integration
    straightforward.
    """
    labels = labels or {}
    tp = tn = fp = fn = 0
    for item in decisions:
        if isinstance(item, dict):
            left, right = str(item["left_id"]), str(item["right_id"])
            actual = labels.get((left, right), labels.get((right, left)))
            predicted_name = item.get("decision", "")
        else:
            left, right = str(item.left_id), str(item.right_id)
            actual = labels.get((left, right), labels.get((right, left)))
            predicted_name = item.decision
        if actual is None:
            continue
        predicted = str(predicted_name).upper() == "EQUIVALENT"
        if predicted and actual: tp += 1
        elif predicted: fp += 1
        elif actual: fn += 1
        else: tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return EvaluationMetrics(tp, tn, fp, fn, precision, recall, f1)

