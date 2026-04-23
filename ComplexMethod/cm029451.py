def to_serializable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value

    if isinstance(value, dict):
        return {ensure_str(k): to_serializable(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [to_serializable(v) for v in value]

    value_as_dict = as_dict(value)
    if value_as_dict is not None:
        return to_serializable(value_as_dict)

    return ensure_str(value)