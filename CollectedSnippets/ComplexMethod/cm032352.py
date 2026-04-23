def _validate_expected_type(expected_type: str, value, path: str = "") -> None:
    etype = _normalize_expected_type(expected_type)
    if not etype or etype.lower() == "any":
        return

    value = normalize_output_value(value)

    if etype.startswith("Array<") and etype.endswith(">"):
        inner_type = etype[6:-1].strip()
        if not isinstance(value, list):
            raise ContractError(
                f"CodeExec contract mismatch at {path or 'value'}: expected type {etype}, got {infer_actual_type(value)}"
            )
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            _validate_expected_type(inner_type, item, child_path)
        return

    actual_type = infer_actual_type(value)
    if etype == "String":
        valid = isinstance(value, str)
    elif etype == "Number":
        valid = _is_number(value)
    elif etype == "Boolean":
        valid = isinstance(value, bool)
    elif etype == "Object":
        valid = isinstance(value, dict)
    elif etype == "Null":
        valid = value is None
    else:
        raise ContractError(f"Unsupported expected type: {expected_type}")

    if not valid:
        raise ContractError(
            f"CodeExec contract mismatch at {path or 'value'}: expected type {etype}, got {actual_type}"
        )