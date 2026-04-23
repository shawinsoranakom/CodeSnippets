def _custom_serializer(schema: Any, *, allow_section: bool) -> Any:
    """Serialize additional types for voluptuous_serialize."""
    from homeassistant import data_entry_flow  # noqa: PLC0415

    from . import selector  # noqa: PLC0415

    if schema is positive_time_period_dict:
        return {"type": "positive_time_period_dict"}

    if schema is string:
        return {"type": "string"}

    if schema is boolean:
        return {"type": "boolean"}

    if isinstance(schema, data_entry_flow.section):
        if not allow_section:
            raise ValueError("Nesting expandable sections is not supported")
        return {
            "type": "expandable",
            "schema": voluptuous_serialize.convert(
                schema.schema,
                custom_serializer=functools.partial(
                    _custom_serializer, allow_section=False
                ),
            ),
            "expanded": not schema.options["collapsed"],
        }

    if isinstance(schema, multi_select):
        return {"type": "multi_select", "options": schema.options}

    if isinstance(schema, selector.Selector):
        return schema.serialize()

    return voluptuous_serialize.UNSUPPORTED