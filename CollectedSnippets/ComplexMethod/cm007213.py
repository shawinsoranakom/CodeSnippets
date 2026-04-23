def _custom_stringify(obj: Any) -> str:
    """Replicate Langflow frontend's customStringify for edge handle data.

    Covers the subset of types used in handle dicts. Uses json.dumps for
    strings to handle escaping correctly.
    """
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, (int, float)):
        return str(obj)
    if isinstance(obj, str):
        import json

        return json.dumps(obj)
    if isinstance(obj, list):
        items = ",".join(_custom_stringify(item) for item in obj)
        return f"[{items}]"
    if isinstance(obj, dict):
        keys = sorted(obj.keys())
        pairs = ",".join(f'"{k}":{_custom_stringify(obj[k])}' for k in keys)
        return f"{{{pairs}}}"
    return str(obj)