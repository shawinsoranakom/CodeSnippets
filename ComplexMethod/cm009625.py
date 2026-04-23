def _create_subset_model_v1(
    name: str,
    model: type[BaseModelV1],
    field_names: list,
    *,
    descriptions: dict | None = None,
    fn_description: str | None = None,
) -> type[BaseModelV1]:
    """Create a Pydantic model with only a subset of model's fields."""
    fields = {}

    for field_name in field_names:
        # Using pydantic v1 so can access __fields__ as a dict.
        field = model.__fields__[field_name]
        t = (
            # this isn't perfect but should work for most functions
            field.outer_type_
            if field.required and not field.allow_none
            else field.outer_type_ | None
        )
        if descriptions and field_name in descriptions:
            field.field_info.description = descriptions[field_name]
        fields[field_name] = (t, field.field_info)

    rtn = cast("type[BaseModelV1]", create_model_v1(name, **fields))  # type: ignore[call-overload]
    rtn.__doc__ = textwrap.dedent(fn_description or model.__doc__ or "")
    return rtn