def _is_tabular(parsed: Any) -> bool:
    """Check if parsed data is in tabular format: [[header], [row1], ...].

    Uses isinstance checks because this is a structural type guard on
    opaque parser output (Any), not duck typing.  A Protocol wouldn't
    help here — we need to verify exact list-of-lists shape.
    """
    if not isinstance(parsed, list) or len(parsed) < 2:
        return False
    header = parsed[0]
    if not isinstance(header, list) or not header:
        return False
    if not all(isinstance(h, str) for h in header):
        return False
    return all(isinstance(row, list) for row in parsed[1:])