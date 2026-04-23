def validate_value(cls, v: Any, info):
        if v is None or isinstance(v, dict):
            return v
        if isinstance(v, Message):
            v = v.text
        elif isinstance(v, Data):
            v = v.data.get(v.text_key, "")
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return {}
            import json

            try:
                parsed = json.loads(v)
            except json.JSONDecodeError as e:
                input_name = info.data.get("name", "unknown")
                msg = f"Could not parse JSON string for input {input_name}: {e}"
                raise ValueError(msg) from None
            if not isinstance(parsed, dict):
                input_name = info.data.get("name", "unknown")
                msg = f"Expected a JSON object for input {input_name}, got {type(parsed).__name__}."
                raise TypeError(msg)
            return parsed
        msg = f"Invalid value type {type(v)} for input {info.data.get('name')}."
        raise TypeError(msg)