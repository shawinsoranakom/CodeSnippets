def parse_value(value: Any, input_type: str) -> Any:
    """Helper function to parse the value based on input type."""
    if value == "":
        return {} if input_type == "DictInput" else value
    if input_type == "IntInput":
        return int(value) if value is not None else None
    if input_type == "FloatInput":
        return float(value) if value is not None else None
    if input_type == "DictInput":
        if isinstance(value, dict):
            return value
        try:
            parsed = _json.loads(value) if value is not None else {}
            return parsed if isinstance(parsed, dict) else {}
        except (ValueError, TypeError):
            return {}
    return value