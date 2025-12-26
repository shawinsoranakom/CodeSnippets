def add_binary_prefix(value: float) -> str:

    for prefix in BinaryUnit:
        numerical_part = value / (2**prefix.value)
        if numerical_part > 1:
            return f"{numerical_part!s} {prefix.name}"
    return str(value)
