def __init__(
        self, value, output_field=None, *, invert=False, prefix=False, weight=None
    ):
        if value == "":
            raise ValueError("Lexeme value cannot be empty.")

        if not isinstance(value, str):
            raise TypeError(
                f"Lexeme value must be a string, got {value.__class__.__name__}."
            )

        if weight is not None and (
            not isinstance(weight, str) or weight.lower() not in {"a", "b", "c", "d"}
        ):
            raise ValueError(
                f"Weight must be one of 'A', 'B', 'C', and 'D', got {weight!r}."
            )

        self.prefix = prefix
        self.invert = invert
        self.weight = weight
        super().__init__(value, output_field=output_field)