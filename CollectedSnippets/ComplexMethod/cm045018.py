def _resolve_dot_path(obj: Any, path: str) -> Any:
    """Resolve a dotted path like ``steps.specify.output.file`` against *obj*.

    Supports dict key access and list indexing (e.g., ``task_list[0]``).
    """
    parts = path.split(".")
    current = obj
    for part in parts:
        # Handle list indexing: name[0]
        idx_match = re.match(r"^([\w-]+)\[(\d+)\]$", part)
        if idx_match:
            key, idx = idx_match.group(1), int(idx_match.group(2))
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
            if isinstance(current, list) and 0 <= idx < len(current):
                current = current[idx]
            else:
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
        if current is None:
            return None
    return current