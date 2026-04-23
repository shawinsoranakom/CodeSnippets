def execute(cls, value) -> io.NodeOutput:
        if isinstance(value, bool):
            float_val = 1.0 if value else 0.0
            int_val = 1 if value else 0
        elif isinstance(value, int):
            float_val = float(value)
            int_val = value
        elif isinstance(value, float):
            float_val = value
            int_val = int(value)
        elif isinstance(value, str):
            text = value.strip()
            if not text:
                raise ValueError("Cannot convert empty string to number.")
            try:
                float_val = float(text)
            except ValueError:
                raise ValueError(
                    f"Cannot convert string to number: {value!r}"
                ) from None
            if not math.isfinite(float_val):
                raise ValueError(
                    f"Cannot convert non-finite value to number: {float_val}"
                )
            try:
                int_val = int(text)
            except ValueError:
                int_val = int(float_val)
        else:
            raise TypeError(
                f"Unsupported input type: {type(value).__name__}"
            )

        if not math.isfinite(float_val):
            raise ValueError(
                f"Cannot convert non-finite value to number: {float_val}"
            )

        return io.NodeOutput(float_val, int_val)