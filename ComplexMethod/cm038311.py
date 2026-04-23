def _extract_types_from_schema(self, schema: Any) -> list[str]:
        """
        Extract all possible types from a JSON schema definition.
        Handles anyOf, oneOf, allOf, type arrays, and enum fields.

        Args:
            schema: The JSON schema definition for a parameter

        Returns:
            List of type strings (e.g., ["string", "integer", "null"])
        """
        if schema is None:
            return ["string"]

        if not isinstance(schema, dict):
            return ["string"]

        types: set[str] = set()

        # Handle direct "type" field
        if "type" in schema:
            type_value = schema["type"]
            if isinstance(type_value, str):
                types.add(type_value)
            elif isinstance(type_value, list):
                for t in type_value:
                    if isinstance(t, str):
                        types.add(t)

        # Handle enum - infer types from enum values
        if "enum" in schema and isinstance(schema["enum"], list) and schema["enum"]:
            for value in schema["enum"]:
                if value is None:
                    types.add("null")
                elif isinstance(value, bool):
                    types.add("boolean")
                elif isinstance(value, int):
                    types.add("integer")
                elif isinstance(value, float):
                    types.add("number")
                elif isinstance(value, str):
                    types.add("string")
                elif isinstance(value, list):
                    types.add("array")
                elif isinstance(value, dict):
                    types.add("object")

        # Handle anyOf, oneOf, allOf - recursively extract types
        for choice_field in ("anyOf", "oneOf", "allOf"):
            if choice_field in schema and isinstance(schema[choice_field], list):
                for choice in schema[choice_field]:
                    extracted = self._extract_types_from_schema(choice)
                    types.update(extracted)

        # If no types found, default to string
        if not types:
            return ["string"]

        return list(types)