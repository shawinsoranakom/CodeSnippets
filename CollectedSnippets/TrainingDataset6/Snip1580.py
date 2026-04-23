def get_schema_from_model_field(
    *,
    field: ModelField,
    model_name_map: ModelNameMap,
    field_mapping: dict[
        tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue
    ],
    separate_input_output_schemas: bool = True,
) -> dict[str, Any]:
    override_mode: Literal["validation"] | None = (
        None
        if (separate_input_output_schemas or _has_computed_fields(field))
        else "validation"
    )
    field_alias = (
        (field.validation_alias or field.alias)
        if field.mode == "validation"
        else (field.serialization_alias or field.alias)
    )

    # This expects that GenerateJsonSchema was already used to generate the definitions
    json_schema = field_mapping[(field, override_mode or field.mode)]
    if "$ref" not in json_schema:
        # TODO remove when deprecating Pydantic v1
        # Ref: https://github.com/pydantic/pydantic/blob/d61792cc42c80b13b23e3ffa74bc37ec7c77f7d1/pydantic/schema.py#L207
        json_schema["title"] = field.field_info.title or field_alias.title().replace(
            "_", " "
        )
    return json_schema