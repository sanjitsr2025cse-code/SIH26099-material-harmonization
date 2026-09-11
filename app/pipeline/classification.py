"""Transparent keyword/rule material-category classification."""
def classify(text: object, categories: dict[str, list[str]] | None = None) -> str | None:
    if not categories:
        return None
    value = str(text or "").lower()
    for category, terms in categories.items():
        if any(term.lower() in value for term in terms):
            return category
    return None
