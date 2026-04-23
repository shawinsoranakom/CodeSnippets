def validate_data(
        cls,
        data: BlockInput,
        exclude_fields: set[str] | None = None,
    ) -> str | None:
        schema = cls.jsonschema()
        if exclude_fields:
            # Drop the excluded fields from both the properties and the
            # ``required`` list so jsonschema doesn't flag them as missing.
            # Used by the dry-run path to skip credentials validation while
            # still validating the remaining block inputs.
            schema = {
                **schema,
                "properties": {
                    k: v
                    for k, v in schema.get("properties", {}).items()
                    if k not in exclude_fields
                },
                "required": [
                    r for r in schema.get("required", []) if r not in exclude_fields
                ],
            }
            data = {k: v for k, v in data.items() if k not in exclude_fields}
        return json.validate_with_jsonschema(
            schema=schema,
            data={k: v for k, v in data.items() if v is not None},
        )