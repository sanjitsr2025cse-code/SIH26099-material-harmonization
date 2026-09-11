"""Human-in-the-loop decisions for uncertain matching candidates."""
from .models import HumanDecision, ReviewItem


class ReviewWorkflow:
    def __init__(self) -> None:
        self.items: dict[str, ReviewItem] = {}

    def add(self, item: ReviewItem) -> ReviewItem:
        self.items[item.review_id] = item
        return item

    def pending(self) -> list[ReviewItem]:
        return [item for item in self.items.values() if item.status == "PENDING"]

    def decide(self, review_id: str, action: str, reviewer: str,
               explanation: str = "", target_cnmc_id: str | None = None) -> ReviewItem:
        item = self.items[review_id]
        action = action.upper()
        if action not in {"APPROVE", "REJECT", "OVERRIDE"}:
            raise ValueError("action must be APPROVE, REJECT, or OVERRIDE")
        if item.status != "PENDING":
            raise ValueError("review item has already been decided")
        item.human_decision = HumanDecision(action, reviewer, explanation, target_cnmc_id)
        item.status = action
        return item

