def add_si_prefix(value: float) -> str:

    prefixes = SIUnit.get_positive() if value > 0 else SIUnit.get_negative()
    for name_prefix, value_prefix in prefixes.items():
        numerical_part = value / (10**value_prefix)
        if numerical_part > 1:
            return f"{numerical_part!s} {name_prefix}"
    return str(value)
