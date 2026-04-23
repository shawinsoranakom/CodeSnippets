def get_body_field(
    *, flat_dependant: Dependant, name: str, embed_body_fields: bool
) -> ModelField | None:
    """
    Get a ModelField representing the request body for a path operation, combining
    all body parameters into a single field if necessary.

    Used to check if it's form data (with `isinstance(body_field, params.Form)`)
    or JSON and to generate the JSON Schema for a request body.

    This is **not** used to validate/parse the request body, that's done with each
    individual body parameter.
    """
    if not flat_dependant.body_params:
        return None
    first_param = flat_dependant.body_params[0]
    if not embed_body_fields:
        return first_param
    model_name = "Body_" + name
    BodyModel = create_body_model(
        fields=flat_dependant.body_params, model_name=model_name
    )
    required = any(
        True for f in flat_dependant.body_params if f.field_info.is_required()
    )
    BodyFieldInfo_kwargs: dict[str, Any] = {
        "annotation": BodyModel,
        "alias": "body",
    }
    if not required:
        BodyFieldInfo_kwargs["default"] = None
    if any(isinstance(f.field_info, params.File) for f in flat_dependant.body_params):
        BodyFieldInfo: type[params.Body] = params.File
    elif any(isinstance(f.field_info, params.Form) for f in flat_dependant.body_params):
        BodyFieldInfo = params.Form
    else:
        BodyFieldInfo = params.Body

        body_param_media_types = [
            f.field_info.media_type
            for f in flat_dependant.body_params
            if isinstance(f.field_info, params.Body)
        ]
        if len(set(body_param_media_types)) == 1:
            BodyFieldInfo_kwargs["media_type"] = body_param_media_types[0]
    final_field = create_model_field(
        name="body",
        type_=BodyModel,
        alias="body",
        field_info=BodyFieldInfo(**BodyFieldInfo_kwargs),
    )
    return final_field