def extract_search_terms_from_steps(
    decomposition_result: DecompositionResult | dict[str, Any],
) -> list[str]:
    """Extract search terms from decomposed instruction steps.

    Analyzes the decomposition result to extract relevant keywords
    for additional library agent searches.

    Args:
        decomposition_result: Result from decompose_goal containing steps

    Returns:
        List of unique search terms extracted from steps
    """
    search_terms: list[str] = []

    if decomposition_result.get("type") != "instructions":
        return search_terms

    steps = decomposition_result.get("steps", [])
    if not steps:
        return search_terms

    step_keys: list[str] = ["description", "action", "block_name", "tool", "name"]

    for step in steps:
        for key in step_keys:
            value = step.get(key)  # type: ignore[union-attr]
            if isinstance(value, str) and len(value) > 3:
                search_terms.append(value)

    seen: set[str] = set()
    unique_terms: list[str] = []
    for term in search_terms:
        term_lower = term.lower()
        if term_lower not in seen:
            seen.add(term_lower)
            unique_terms.append(term)

    return unique_terms