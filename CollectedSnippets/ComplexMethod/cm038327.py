def _convert_param_value_checked(self, value: str, param_type: str) -> Any:
        """Convert parameter value to the correct type."""
        if value.lower() == "null":
            return None

        param_type = param_type.lower()
        if param_type in ["string", "str", "text"]:
            return value
        elif param_type in ["integer", "int"]:
            return int(value)
        elif param_type in ["number", "float"]:
            val = float(value)
            return val if val != int(val) else int(val)
        elif param_type in ["boolean", "bool"]:
            value = value.strip()
            if value.lower() not in ["false", "0", "true", "1"]:
                raise ValueError("Invalid boolean value")
            return value.lower() in ["true", "1"]
        elif param_type in ["object", "array"]:
            return json.loads(value)
        else:
            return json.loads(value)