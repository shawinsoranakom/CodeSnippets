def _create_subset_model_v2(
    name: str,
    model: type[BaseModel],
    field_names: list[str],
    *,
    descriptions: dict | None = None,
    fn_description: str | None = None,
) -> type[BaseModel]:
    """Create a Pydantic model with a subset of the model fields."""
    descriptions_ = descriptions or {}
    fields = {}
    for field_name in field_names:
        field = model.model_fields[field_name]
        description = descriptions_.get(field_name, field.description)
        field_kwargs: dict[str, Any] = {"description": description}
        if field.default_factory is not None:
            field_kwargs["default_factory"] = field.default_factory
        else:
            field_kwargs["default"] = field.default
        field_info = FieldInfoV2(**field_kwargs)
        if field.metadata:
            field_info.metadata = field.metadata
        fields[field_name] = (field.annotation, field_info)

    rtn = cast(
        "type[BaseModel]",
        _create_model_base(  # type: ignore[call-overload]
            name, **fields, __config__=ConfigDict(arbitrary_types_allowed=True)
        ),
    )

    # TODO(0.3): Determine if there is a more "pydantic" way to preserve annotations.
    # This is done to preserve __annotations__ when working with pydantic 2.x
    # and using the Annotated type with TypedDict.
    # Comment out the following line, to trigger the relevant test case.
    selected_annotations = [
        (name, annotation)
        for name, annotation in model.__annotations__.items()
        if name in field_names
    ]

    rtn.__annotations__ = dict(selected_annotations)
    rtn.__doc__ = textwrap.dedent(fn_description or model.__doc__ or "")
    return rtn