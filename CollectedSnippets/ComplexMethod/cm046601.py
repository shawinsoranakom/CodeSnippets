def _parse_oxc_spec(
    *,
    column: dict[str, Any],
) -> OxcLocalCallableValidatorSpec | None:
    if str(column.get("column_type") or "").strip() != "validation":
        return None
    if str(column.get("validator_type") or "").strip() != "local_callable":
        return None

    params = column.get("validator_params")
    if not isinstance(params, dict):
        return None

    fn_raw = params.get("validation_function")
    fn_name = fn_raw.strip() if isinstance(fn_raw, str) else ""
    if not fn_name.startswith(OXC_VALIDATION_FN_MARKER):
        return None

    name = str(column.get("name") or "").strip()
    if not name:
        return None

    target_columns_raw = column.get("target_columns")
    target_columns = (
        [
            value.strip()
            for value in target_columns_raw
            if isinstance(value, str) and value.strip()
        ]
        if isinstance(target_columns_raw, list)
        else []
    )
    if not target_columns:
        return None

    code_lang, validation_mode, code_shape = _parse_oxc_validation_marker(fn_name)
    batch_size = _parse_batch_size(column.get("batch_size"))
    drop = bool(column.get("drop") is True)

    return OxcLocalCallableValidatorSpec(
        name = name,
        drop = drop,
        target_columns = target_columns,
        batch_size = batch_size,
        code_lang = code_lang,
        validation_mode = validation_mode,
        code_shape = code_shape,
    )