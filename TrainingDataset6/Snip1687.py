async def _extract_form_body(
    body_fields: list[ModelField],
    received_body: FormData,
) -> dict[str, Any]:
    values = {}

    for field in body_fields:
        value = _get_multidict_value(field, received_body)
        field_info = field.field_info
        if (
            isinstance(field_info, params.File)
            and is_bytes_or_nonable_bytes_annotation(field.field_info.annotation)
            and isinstance(value, UploadFile)
        ):
            value = await value.read()
        elif (
            is_bytes_sequence_annotation(field.field_info.annotation)
            and isinstance(field_info, params.File)
            and value_is_sequence(value)
        ):
            # For types
            assert isinstance(value, sequence_types)
            results: list[bytes | str] = []
            for sub_value in value:
                results.append(await sub_value.read())
            value = serialize_sequence_value(field=field, value=results)
        if value is not None:
            values[get_validation_alias(field)] = value
    field_aliases = {get_validation_alias(field) for field in body_fields}
    for key in received_body.keys():
        if key not in field_aliases:
            param_values = received_body.getlist(key)
            if len(param_values) == 1:
                values[key] = param_values[0]
            else:
                values[key] = param_values
    return values