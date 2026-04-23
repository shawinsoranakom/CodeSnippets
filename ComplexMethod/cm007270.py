def _resolve_refs(value: Any, results: list[Any]) -> Any:
    """Replace $N.field references with actual values from previous results."""
    if isinstance(value, str):
        match = _REF_PATTERN.match(value)
        if match:
            idx, field = int(match.group(1)), match.group(2)
            if idx >= len(results):
                msg = f"Reference ${idx} is out of range (only {len(results)} results so far)"
                raise ValueError(msg)
            result = results[idx]
            if isinstance(result, dict) and field in result:
                return result[field]
            msg = f"${idx}.{field}: field '{field}' not found in result {idx}"
            raise ValueError(msg)
        return value
    if isinstance(value, dict):
        return {k: _resolve_refs(v, results) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_refs(v, results) for v in value]
    return value