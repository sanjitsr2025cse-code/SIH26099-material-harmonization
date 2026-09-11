"""Deterministic in-memory clustering, canonical registry, and mappings."""
from typing import Any, Iterable
from app.harmonization.matching import MaterialMatcher
from app.harmonization.service import harmonize_records
from .models import AIDecision, CanonicalMaterial, MappingEvent, ReviewItem
from .review import ReviewWorkflow


class MaterialRegistry:
    """Governed registry built from existing pairwise matching decisions."""

    def __init__(self, matcher: MaterialMatcher | None = None) -> None:
        self.matcher = matcher or MaterialMatcher()
        self.records: dict[str, dict[str, Any]] = {}
        self.canonicals: dict[str, CanonicalMaterial] = {}
        self.mappings: dict[tuple[str, str], str] = {}
        self.mapping_history: list[MappingEvent] = []
        self.decisions: list[AIDecision] = []
        self.review = ReviewWorkflow()
        self.review_workflow = self.review
        self._next_cnmc = 1
        self._next_mapping = 1

    def ingest(self, records: Iterable[dict[str, Any]], harmonize: bool = True) -> list[CanonicalMaterial]:
        prepared = harmonize_records(records) if harmonize else [dict(r) for r in records]
        for index, record in enumerate(prepared):
            value = dict(record)
            record_id = str(value.get("record_id") or value.get("id") or f"record-{index + 1}")
            value["record_id"] = record_id
            self.records[record_id] = value
        self._cluster()
        return self.list_canonicals()

    register = ingest

    def _cluster(self) -> None:
        ids = sorted(self.records)
        parent = {key: key for key in ids}
        def find(key: str) -> str:
            while parent[key] != key:
                parent[key] = parent[parent[key]]
                key = parent[key]
            return key
        def union(a: str, b: str) -> None:
            a, b = find(a), find(b)
            if a != b: parent[max(a, b)] = min(a, b)
        self.decisions.clear()
        for position, left_id in enumerate(ids):
            for right_id in ids[position + 1:]:
                result = self.matcher.compare(self.records[left_id], self.records[right_id])
                decision = AIDecision(left_id, right_id, result.decision, result.confidence,
                                      tuple(result.reasons), result.semantic_score,
                                      result.attribute_score, result.terminology_score)
                self.decisions.append(decision)
                if result.decision == "EQUIVALENT":
                    union(left_id, right_id)
                elif result.decision == "REVIEW":
                    key = f"review-{left_id}-{right_id}"
                    existing_review = self.review.items.get(key)
                    if existing_review and existing_review.status == "APPROVE":
                        union(left_id, right_id)
                    elif not existing_review:
                        self.review.add(ReviewItem(key, left_id, right_id, decision))
        groups: dict[str, list[str]] = {}
        for record_id in ids:
            groups.setdefault(find(record_id), []).append(record_id)
        old_by_members = {material.member_ids: material for material in self.canonicals.values()}
        new: dict[str, CanonicalMaterial] = {}
        for members in sorted(groups.values(), key=lambda values: tuple(values)):
            member_ids = tuple(sorted(members))
            existing = old_by_members.get(member_ids)
            cnmc_id = existing.cnmc_id if existing else f"CNMC-{self._next_cnmc:06d}"
            if not existing: self._next_cnmc += 1
            canonical_id = member_ids[0]
            canonical = dict(self.records[canonical_id])
            canonical["record_id"] = canonical_id
            canonical["cnmc_id"] = cnmc_id
            new[cnmc_id] = CanonicalMaterial(cnmc_id, canonical, member_ids)
        self.canonicals = new
        self._refresh_mappings()

    def _refresh_mappings(self) -> None:
        for material in self.canonicals.values():
            for member_id in material.member_ids:
                record = self.records[member_id]
                source = str(record.get("source_system", record.get("source", "default")))
                code = str(record.get("material_code", record.get("source_material_code", member_id)))
                key = (source, code)
                if self.mappings.get(key) == material.cnmc_id:
                    continue
                self.mappings[key] = material.cnmc_id
                self.mapping_history.append(MappingEvent(
                    code, source, material.cnmc_id, member_id, "MAPPED", self._next_mapping))
                self._next_mapping += 1

    def list_canonicals(self) -> list[CanonicalMaterial]:
        return sorted(self.canonicals.values(), key=lambda material: material.cnmc_id)

    def candidates(self) -> list[ReviewItem]:
        return self.review.pending()

    def decide_review(self, review_id: str, action: str, reviewer: str,
                      explanation: str = "", target_cnmc_id: str | None = None) -> ReviewItem:
        item = self.review.decide(review_id, action, reviewer, explanation, target_cnmc_id)
        if action.upper() == "APPROVE":
            self._force_merge(item.left_id, item.right_id)
        elif action.upper() == "OVERRIDE" and target_cnmc_id:
            self._map_record(item.right_id, target_cnmc_id)
        return item

    def _force_merge(self, left_id: str, right_id: str) -> None:
        left = next((c for c in self.canonicals.values() if left_id in c.member_ids), None)
        right = next((c for c in self.canonicals.values() if right_id in c.member_ids), None)
        if not left or not right or left.cnmc_id == right.cnmc_id:
            return
        merged = tuple(sorted(set(left.member_ids + right.member_ids)))
        canonical = dict(self.records[merged[0]])
        canonical["cnmc_id"] = left.cnmc_id
        self.canonicals.pop(right.cnmc_id, None)
        self.canonicals[left.cnmc_id] = CanonicalMaterial(left.cnmc_id, canonical, merged)
        self._refresh_mappings()

    def _map_record(self, record_id: str, cnmc_id: str) -> None:
        if cnmc_id not in self.canonicals:
            raise KeyError(f"unknown CNMC identifier: {cnmc_id}")
        material = self.canonicals[cnmc_id]
        if record_id in material.member_ids:
            return
        previous = next((candidate for candidate in self.canonicals.values()
                         if record_id in candidate.member_ids), None)
        if previous:
            remaining = tuple(member for member in previous.member_ids if member != record_id)
            if remaining:
                self.canonicals[previous.cnmc_id] = CanonicalMaterial(
                    previous.cnmc_id, previous.record, remaining)
            else:
                self.canonicals.pop(previous.cnmc_id, None)
        merged = tuple(sorted(material.member_ids + (record_id,)))
        canonical = dict(material.record)
        self.canonicals[cnmc_id] = CanonicalMaterial(cnmc_id, canonical, merged)
        self._refresh_mappings()

    def search(self, text: str) -> list[CanonicalMaterial]:
        query = text.casefold()
        return [material for material in self.list_canonicals()
                if query in str(material.record.get("description", material.record.get("normalized_description", ""))).casefold()
                or query in material.cnmc_id.casefold()]

    def statistics(self) -> dict[str, int]:
        return {"records": len(self.records), "canonical_materials": len(self.canonicals),
                "mappings": len(self.mappings), "mapping_history": len(self.mapping_history),
                "pending_reviews": len(self.candidates())}
