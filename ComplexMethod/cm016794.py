def _contains_self_unequal(obj: Any) -> bool:
    # Local cache matches by ==. Values where not (x == x) (NaN, etc.) will
    # never hit locally, but serialized form would match externally. Skip these.
    try:
        if not (obj == obj):
            return True
    except Exception:
        return True
    if isinstance(obj, (frozenset, tuple, list, set)):
        return any(_contains_self_unequal(item) for item in obj)
    if isinstance(obj, dict):
        return any(_contains_self_unequal(k) or _contains_self_unequal(v) for k, v in obj.items())
    if hasattr(obj, 'value'):
        return _contains_self_unequal(obj.value)
    return False