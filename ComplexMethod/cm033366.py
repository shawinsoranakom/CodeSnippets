def auto_cast_value(value, expected_type):
        """Convert string values into schema type when possible."""

        # Non-string values already good
        if not isinstance(value, str):
            return value

        v = value.strip()

        # Boolean
        if expected_type == "boolean":
            if v.lower() in ["true", "1"]:
                return True
            if v.lower() in ["false", "0"]:
                return False
            raise Exception(f"Cannot convert '{value}' to boolean")

        # Number
        if expected_type == "number":
            # integer
            if v.isdigit() or (v.startswith("-") and v[1:].isdigit()):
                return int(v)

            # float
            try:
                return float(v)
            except Exception:
                raise Exception(f"Cannot convert '{value}' to number")

        # Object
        if expected_type == "object":
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    return parsed
                else:
                    raise Exception("JSON is not an object")
            except Exception:
                raise Exception(f"Cannot convert '{value}' to object")

        # Array <T>
        if expected_type.startswith("array"):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                else:
                    raise Exception("JSON is not an array")
            except Exception:
                raise Exception(f"Cannot convert '{value}' to array")

        # String (accept original)
        if expected_type == "string":
            return value

        # File
        if expected_type == "file":
            return value
        # Default: do nothing
        return value