def _validate_value_with_model_field(
    *, field: ModelField, value: Any, values: dict[str, Any], loc: tuple[str, ...]
) -> tuple[Any, list[Any]]:
    if value is None:
        if field.field_info.is_required():
            return None, [get_missing_field_error(loc=loc)]
        else:
            return deepcopy(field.default), []
    return field.validate(value, values, loc=loc)