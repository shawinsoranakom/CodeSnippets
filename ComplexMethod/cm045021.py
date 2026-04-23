def _safe_compare(left: Any, right: Any, op: str) -> bool:
    """Safely compare two values, coercing types when possible."""
    try:
        if isinstance(left, str):
            left = float(left) if "." in left else int(left)
        if isinstance(right, str):
            right = float(right) if "." in right else int(right)
    except (ValueError, TypeError):
        return False
    try:
        if op == ">":
            return left > right  # type: ignore[operator]
        if op == "<":
            return left < right  # type: ignore[operator]
        if op == ">=":
            return left >= right  # type: ignore[operator]
        if op == "<=":
            return left <= right  # type: ignore[operator]
    except TypeError:
        return False
    return False