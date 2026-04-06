def _get_openapi_operation_parameters(
    *,
    dependant: Dependant,
    model_name_map: ModelNameMap,
    field_mapping: dict[
        tuple[ModelField, Literal["validation", "serialization"]], dict[str, Any]
    ],
    separate_input_output_schemas: bool = True,
) -> list[dict[str, Any]]:
    parameters = []
    flat_dependant = get_flat_dependant(dependant, skip_repeats=True)
    path_params = _get_flat_fields_from_params(flat_dependant.path_params)
    query_params = _get_flat_fields_from_params(flat_dependant.query_params)
    header_params = _get_flat_fields_from_params(flat_dependant.header_params)
    cookie_params = _get_flat_fields_from_params(flat_dependant.cookie_params)
    parameter_groups = [
        (ParamTypes.path, path_params),
        (ParamTypes.query, query_params),
        (ParamTypes.header, header_params),
        (ParamTypes.cookie, cookie_params),
    ]
    default_convert_underscores = True
    if len(flat_dependant.header_params) == 1:
        first_field = flat_dependant.header_params[0]
        if lenient_issubclass(first_field.field_info.annotation, BaseModel):
            default_convert_underscores = getattr(
                first_field.field_info, "convert_underscores", True
            )
    for param_type, param_group in parameter_groups:
        for param in param_group:
            field_info = param.field_info
            # field_info = cast(Param, field_info)
            if not getattr(field_info, "include_in_schema", True):
                continue
            param_schema = get_schema_from_model_field(
                field=param,
                model_name_map=model_name_map,
                field_mapping=field_mapping,
                separate_input_output_schemas=separate_input_output_schemas,
            )
            name = get_validation_alias(param)
            convert_underscores = getattr(
                param.field_info,
                "convert_underscores",
                default_convert_underscores,
            )
            if (
                param_type == ParamTypes.header
                and name == param.name
                and convert_underscores
            ):
                name = param.name.replace("_", "-")

            parameter = {
                "name": name,
                "in": param_type.value,
                "required": param.field_info.is_required(),
                "schema": param_schema,
            }
            if field_info.description:
                parameter["description"] = field_info.description
            openapi_examples = getattr(field_info, "openapi_examples", None)
            example = getattr(field_info, "example", None)
            if openapi_examples:
                parameter["examples"] = jsonable_encoder(openapi_examples)
            elif example is not _Unset:
                parameter["example"] = jsonable_encoder(example)
            if getattr(field_info, "deprecated", None):
                parameter["deprecated"] = True
            parameters.append(parameter)
    return parameters