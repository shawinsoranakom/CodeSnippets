def get_type_str(value: Any) -> str:
    """Get a detailed string representation of the type of a value.

    Handles special cases and provides more specific type information.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        # Check if string is actually a date/datetime
        if any(date_pattern in value.lower() for date_pattern in ["date", "time", "yyyy", "mm/dd", "dd/mm", "yyyy-mm"]):
            return "str(possible_date)"
        # Check if it's a JSON string
        try:
            json.loads(value)
            return "str(json)"
        except (json.JSONDecodeError, TypeError):
            pass
        else:
            return "str"
    if isinstance(value, list | tuple | set):
        return infer_list_type(list(value))
    if isinstance(value, dict):
        return "dict"
    # Handle custom objects
    return type(value).__name__