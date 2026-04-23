def _node_display_name(node: dict[str, Any]) -> str:
    """Prefer the user-set label (``input_default.name`` / ``metadata.title``);
    fall back to the block id."""
    defaults = node.get("input_default") or {}
    metadata = node.get("metadata") or {}
    for key in ("name", "title", "label"):
        value = defaults.get(key) or metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    block_id = node.get("block_id") or ""
    return block_id or "unknown"