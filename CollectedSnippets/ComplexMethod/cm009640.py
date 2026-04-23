def _recursive_set_additional_properties_false(
    schema: dict[str, Any],
) -> dict[str, Any]:
    if isinstance(schema, dict):
        # Check if 'required' is a key at the current level or if the schema is empty,
        # in which case additionalProperties still needs to be specified.
        if (
            "required" in schema
            or ("properties" in schema and not schema["properties"])
            # Since Pydantic 2.11, it will always add `additionalProperties: True`
            # for arbitrary dictionary schemas
            # See: https://pydantic.dev/articles/pydantic-v2-11-release#changes
            # If it is already set to True, we need override it to False
            or "additionalProperties" in schema
        ):
            schema["additionalProperties"] = False

        # Recursively check 'properties' and 'items' if they exist
        if "anyOf" in schema:
            for sub_schema in schema["anyOf"]:
                _recursive_set_additional_properties_false(sub_schema)
        if "properties" in schema:
            for sub_schema in schema["properties"].values():
                _recursive_set_additional_properties_false(sub_schema)
        if "items" in schema:
            _recursive_set_additional_properties_false(schema["items"])

    return schema