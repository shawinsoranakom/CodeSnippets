def _json_to_list(value: Any) -> list[str]:
    """Convert Json field to list[str], handling None.

    Also handles legacy dict-format rows (e.g. ``{"Learn": [...], "Create": [...]}``
    from the reverted themed-prompts feature) by flattening all values into a single
    list so existing personalised data isn't silently lost.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return cast(list[str], value)
    if isinstance(value, dict):
        # Legacy themed-prompt format: flatten all string values from all categories.
        logger.debug(
            "_json_to_list: flattening legacy dict-format value (keys=%s)",
            list(value.keys()),
        )
        return [
            item
            for vals in value.values()
            if isinstance(vals, list)
            for item in vals
            if isinstance(item, str)
        ]
    return []