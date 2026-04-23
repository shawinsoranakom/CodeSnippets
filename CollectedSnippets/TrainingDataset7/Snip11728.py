def __init__(self, expression, length, fill_text=Value(" "), **extra):
        if (
            not hasattr(length, "resolve_expression")
            and length is not None
            and length < 0
        ):
            raise ValueError("'length' must be greater or equal to 0.")
        super().__init__(expression, length, fill_text, **extra)