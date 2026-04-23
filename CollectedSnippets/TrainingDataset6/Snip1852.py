def create_model_field(
    name: str,
    type_: Any,
    default: Any | None = Undefined,
    field_info: FieldInfo | None = None,
    alias: str | None = None,
    mode: Literal["validation", "serialization"] = "validation",
) -> ModelField:
    if annotation_is_pydantic_v1(type_):
        raise PydanticV1NotSupportedError(
            "pydantic.v1 models are no longer supported by FastAPI."
            f" Please update the response model {type_!r}."
        )
    field_info = field_info or FieldInfo(annotation=type_, default=default, alias=alias)
    try:
        return v2.ModelField(mode=mode, name=name, field_info=field_info)
    except PydanticSchemaGenerationError:
        raise fastapi.exceptions.FastAPIError(
            _invalid_args_message.format(type_=type_)
        ) from None