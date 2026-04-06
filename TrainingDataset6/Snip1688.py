async def request_body_to_args(
    body_fields: list[ModelField],
    received_body: dict[str, Any] | FormData | bytes | None,
    embed_body_fields: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    values: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []
    assert body_fields, "request_body_to_args() should be called with fields"
    single_not_embedded_field = len(body_fields) == 1 and not embed_body_fields
    first_field = body_fields[0]
    body_to_process = received_body

    fields_to_extract: list[ModelField] = body_fields

    if (
        single_not_embedded_field
        and lenient_issubclass(first_field.field_info.annotation, BaseModel)
        and isinstance(received_body, FormData)
    ):
        fields_to_extract = get_cached_model_fields(first_field.field_info.annotation)

    if isinstance(received_body, FormData):
        body_to_process = await _extract_form_body(fields_to_extract, received_body)

    if single_not_embedded_field:
        loc: tuple[str, ...] = ("body",)
        v_, errors_ = _validate_value_with_model_field(
            field=first_field, value=body_to_process, values=values, loc=loc
        )
        return {first_field.name: v_}, errors_
    for field in body_fields:
        loc = ("body", get_validation_alias(field))
        value: Any | None = None
        if body_to_process is not None and not isinstance(body_to_process, bytes):
            try:
                value = body_to_process.get(get_validation_alias(field))
            # If the received body is a list, not a dict
            except AttributeError:
                errors.append(get_missing_field_error(loc))
                continue
        v_, errors_ = _validate_value_with_model_field(
            field=field, value=value, values=values, loc=loc
        )
        if errors_:
            errors.extend(errors_)
        else:
            values[field.name] = v_
    return values, errors