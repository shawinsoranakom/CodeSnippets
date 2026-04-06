def get_openapi_operation_request_body(
    *,
    body_field: ModelField | None,
    model_name_map: ModelNameMap,
    field_mapping: dict[
        tuple[ModelField, Literal["validation", "serialization"]], dict[str, Any]
    ],
    separate_input_output_schemas: bool = True,
) -> dict[str, Any] | None:
    if not body_field:
        return None
    assert isinstance(body_field, ModelField)
    body_schema = get_schema_from_model_field(
        field=body_field,
        model_name_map=model_name_map,
        field_mapping=field_mapping,
        separate_input_output_schemas=separate_input_output_schemas,
    )
    field_info = cast(Body, body_field.field_info)
    request_media_type = field_info.media_type
    required = body_field.field_info.is_required()
    request_body_oai: dict[str, Any] = {}
    if required:
        request_body_oai["required"] = required
    request_media_content: dict[str, Any] = {"schema": body_schema}
    if field_info.openapi_examples:
        request_media_content["examples"] = jsonable_encoder(
            field_info.openapi_examples
        )
    elif field_info.example is not _Unset:
        request_media_content["example"] = jsonable_encoder(field_info.example)
    request_body_oai["content"] = {request_media_type: request_media_content}
    return request_body_oai