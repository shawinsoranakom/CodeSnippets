def _json_body_matcher(r1: Any, r2: Any) -> None:
    """Match request bodies as parsed JSON, ignoring key order."""
    b1 = r1.body or b""
    b2 = r2.body or b""
    if isinstance(b1, bytes):
        b1 = b1.decode("utf-8")
    if isinstance(b2, bytes):
        b2 = b2.decode("utf-8")
    try:
        j1 = json.loads(b1)
        j2 = json.loads(b2)
    except (json.JSONDecodeError, ValueError):
        assert b1 == b2, f"body mismatch (non-JSON):\n{b1}\n!=\n{b2}"
        return
    assert j1 == j2, f"body mismatch:\n{j1}\n!=\n{j2}"