def _convert_param_value_with_types(
        self, value: str, param_types: list[str]
    ) -> Any:
        """
        Convert parameter value to the correct type based on a list of possible types.
        Tries each type in order until one succeeds.

        Args:
            value: The string value to convert
            param_types: List of possible type strings

        Returns:
            The converted value
        """
        # Check if the VALUE itself indicates null (not just if null is allowed)
        if value.lower() in ("null", "none", "nil"):
            return None

        # Normalize types
        normalized_types = [t.lower() for t in param_types]

        # Try each type in order of preference (most specific first, string as fallback)
        # Priority: integer > number > boolean > object > array > string
        type_priority = [
            "integer",
            "int",
            "number",
            "float",
            "boolean",
            "bool",
            "object",
            "array",
            "string",
            "str",
            "text",
        ]

        for param_type in type_priority:
            if param_type not in normalized_types:
                continue

            if param_type in ["string", "str", "text"]:
                return value
            elif param_type in ["integer", "int"]:
                try:
                    return int(value)
                except (ValueError, TypeError):
                    continue
            elif param_type in ["number", "float"]:
                try:
                    val = float(value)
                    return val if val != int(val) else int(val)
                except (ValueError, TypeError):
                    continue
            elif param_type in ["boolean", "bool"]:
                lower_val = value.lower().strip()
                if lower_val in ["true", "1", "yes", "on"]:
                    return True
                elif lower_val in ["false", "0", "no", "off"]:
                    return False
                continue
            elif param_type in ["object", "array"]:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    continue

        # Fallback: try JSON parse, then return as string
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value