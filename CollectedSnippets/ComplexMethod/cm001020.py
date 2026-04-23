def _parse_one(item: Any, idx: int) -> ClarifyingQuestion | None:
    """Parse a single question item, returning None for invalid entries."""
    if not isinstance(item, dict):
        logger.warning("ask_question: skipping non-dict item at index %d", idx)
        return None

    text = item.get("question")
    if not isinstance(text, str) or not text.strip():
        logger.warning(
            "ask_question: skipping item at index %d with missing/empty question",
            idx,
        )
        return None

    raw_keyword = item.get("keyword")
    keyword = (
        str(raw_keyword).strip()
        if raw_keyword is not None and str(raw_keyword).strip()
        else f"question-{idx}"
    )

    raw_options = item.get("options")
    options = (
        [str(o) for o in raw_options if o is not None and str(o).strip()]
        if isinstance(raw_options, list)
        else []
    )

    return ClarifyingQuestion(
        question=text.strip(),
        keyword=keyword,
        example=", ".join(options) if options else None,
    )