def filter_value(value):
        if (
            isinstance(value, str)
            and len(value) > 100
            and ("," in value or "/" in value)
        ):
            # Likely base64 data, truncate it
            return value[:20] + "..."
        elif isinstance(value, dict):
            return {k: filter_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [filter_value(item) for item in value]
        return value