def _is_json_field(field: ModelField) -> bool:
    return any(type(item) is Json for item in field.field_info.metadata)