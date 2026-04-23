def _get_multidict_value(
    field: ModelField, values: Mapping[str, Any], alias: str | None = None
) -> Any:
    alias = alias or get_validation_alias(field)
    if (
        (not _is_json_field(field))
        and field_annotation_is_sequence(field.field_info.annotation)
        and isinstance(values, (ImmutableMultiDict, Headers))
    ):
        value = values.getlist(alias)
    else:
        value = values.get(alias, None)
    if (
        value is None
        or (
            isinstance(field.field_info, params.Form)
            and isinstance(value, str)  # For type checks
            and value == ""
        )
        or (
            field_annotation_is_sequence(field.field_info.annotation)
            and len(value) == 0
        )
    ):
        if field.field_info.is_required():
            return
        else:
            return deepcopy(field.default)
    return value