def replace_all_of_with_ref(schema: Any) -> None:
    if isinstance(schema, dict):
        # If the schema has an allOf key with a single item that contains a $ref
        if (
            "allOf" in schema
            and len(schema["allOf"]) == 1
            and "$ref" in schema["allOf"][0]
        ):
            schema["$ref"] = schema["allOf"][0]["$ref"]
            del schema["allOf"]
            if "default" in schema and schema["default"] is None:
                del schema["default"]
        else:
            # Recursively process nested schemas
            for value in schema.values():
                if isinstance(value, (dict, list)):
                    replace_all_of_with_ref(value)
    elif isinstance(schema, list):
        for item in schema:
            replace_all_of_with_ref(item)