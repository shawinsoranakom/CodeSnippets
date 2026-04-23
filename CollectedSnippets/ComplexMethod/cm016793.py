def _canonicalize(obj: Any) -> Any:
    # Convert to canonical JSON-serializable form with deterministic ordering.
    # Frozensets have non-deterministic iteration order between Python sessions.
    # Raises ValueError for non-cacheable types (Unhashable, unknown) so that
    # _serialize_cache_key returns None and external caching is skipped.
    if isinstance(obj, frozenset):
        return ("__frozenset__", sorted(
            [_canonicalize(item) for item in obj],
            key=lambda x: json.dumps(x, sort_keys=True)
        ))
    elif isinstance(obj, set):
        return ("__set__", sorted(
            [_canonicalize(item) for item in obj],
            key=lambda x: json.dumps(x, sort_keys=True)
        ))
    elif isinstance(obj, tuple):
        return ("__tuple__", [_canonicalize(item) for item in obj])
    elif isinstance(obj, list):
        return [_canonicalize(item) for item in obj]
    elif isinstance(obj, dict):
        return {"__dict__": sorted(
            [[_canonicalize(k), _canonicalize(v)] for k, v in obj.items()],
            key=lambda x: json.dumps(x, sort_keys=True)
        )}
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return (type(obj).__name__, obj)
    elif isinstance(obj, bytes):
        return ("__bytes__", obj.hex())
    else:
        raise ValueError(f"Cannot canonicalize type: {type(obj).__name__}")