def _try_convert_value(value: Any, expected_type: type, field_name: str, tool_name: str) -> Any:
    """Try to convert value to expected type. Raise ValueError with clear message on failure."""

    def _err(type_desc: str, detail: str) -> ValueError:
        msg = f"Tool '{tool_name}': Parameter '{field_name}' expects {type_desc} {detail}"
        return ValueError(msg)

    expected_type_desc = expected_type.__name__

    if value is None and expected_type in (int, float, bool, dict, list):
        raise _err(expected_type_desc, "but received None.")

    # return correctly typed value, but handle the
    # special case of bool as this is a subclass of int
    # we'll NOT return but raise an error
    if isinstance(value, expected_type) and not (expected_type is int and isinstance(value, bool)):
        return value

    # return custom classes as is
    if expected_type not in (dict, list, int, float, bool):
        return value

    if expected_type in (dict, list):
        expected_type_desc = "object (dict)" if expected_type is dict else "array (list)"
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as e:
                raise _err(expected_type_desc, f"but received invalid JSON string {value!r}; {e}") from e
            if not isinstance(parsed, expected_type):
                raise _err(expected_type_desc, f"but JSON parsed to {type(parsed).__name__}.")
            return parsed

    elif expected_type is int:
        expected_type_desc = "integer (int)"
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError as e:
                raise _err(expected_type_desc, f"but received string: {value!r}; could not convert.") from e

    elif expected_type is float:
        expected_type_desc = "number (float)"
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError as e:
                raise _err(expected_type_desc, f"but received string: {value!r}; could not convert.") from e

    elif expected_type is bool and isinstance(value, str):
        expected_type_desc = "boolean (bool)"
        lower = value.strip().lower()
        if lower in ("true", "1", "yes"):
            return True
        if lower in ("false", "0", "no"):
            return False

    detail = f"but received {type(value).__name__}: {value!r}; could not convert."
    raise _err(expected_type_desc, detail)