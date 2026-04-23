def infer_actual_type(value) -> str:
    value = normalize_output_value(value)
    if value is None:
        return "Null"
    if isinstance(value, bool):
        return "Boolean"
    if _is_number(value):
        return "Number"
    if isinstance(value, str):
        return "String"
    if isinstance(value, dict):
        return "Object"
    if isinstance(value, list):
        if not value:
            return "Array<Any>"
        inferred = {infer_actual_type(item) for item in value}
        if len(inferred) == 1:
            return f"Array<{inferred.pop()}>"
        return "Array<Any>"
    return "Any"