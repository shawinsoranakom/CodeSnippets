def is_array_value_field_name(obj: object) -> TypeGuard[ArrayValueFieldName]:
    return obj in ARRAY_VALUE_FIELD_NAMES