def validate_value(cls, v: Any, info):
        """Validates the given value and returns the processed value.

        Args:
            v (Any): The value to be validated.
            info: Additional information about the input.

        Returns:
            The processed value.

        Raises:
            ValueError: If the value is not of a valid type or if the input is missing a required key.
        """
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        if isinstance(v, Message):
            v = v.text
        elif isinstance(v, Data):
            v = v.data.get(v.text_key, "")
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return 0
            try:
                return int(v)
            except ValueError:
                pass
            try:
                return int(float(v))
            except ValueError:
                input_name = info.data.get("name", "unknown")
                msg = f"Could not convert '{v}' to integer for input {input_name}."
                raise ValueError(msg) from None
        if not v:
            return 0
        msg = f"Invalid value type {type(v)} for input {info.data.get('name')}."
        raise ValueError(msg)