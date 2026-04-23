def _has_computed_fields(field: ModelField) -> bool:
    computed_fields = field._type_adapter.core_schema.get("schema", {}).get(
        "computed_fields", []
    )
    return len(computed_fields) > 0