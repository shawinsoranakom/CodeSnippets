def _convert_param_value(self, param_value: str, param_type: str) -> Any:
        """Convert value based on parameter type
        Args:
            param_value: Parameter value
            param_type: Parameter type

        Returns:
            Converted value
        """
        if param_value.lower() == "null":
            return None

        param_type = param_type.strip().lower()
        if param_type in ["string", "str", "text", "varchar", "char", "enum"]:
            return param_value
        elif (
            param_type.startswith("int")
            or param_type.startswith("uint")
            or param_type.startswith("long")
            or param_type.startswith("short")
            or param_type.startswith("unsigned")
        ):
            try:
                return int(param_value)
            except (ValueError, TypeError):
                logger.warning(
                    "Parsed value '%s' is not an integer, degenerating to string.",
                    param_value,
                )
            return param_value
        elif param_type.startswith("num") or param_type.startswith("float"):
            try:
                float_param_value: float = float(param_value)
                return (
                    float_param_value
                    if float_param_value - int(float_param_value) != 0
                    else int(float_param_value)
                )
            except (ValueError, TypeError):
                logger.warning(
                    "Parsed value '%s' is not a float, degenerating to string.",
                    param_value,
                )
            return param_value
        elif param_type in ["boolean", "bool", "binary"]:
            param_value = param_value.lower()
            return param_value == "true"
        else:
            return param_value