def convert_si_prefix(
    known_amount: float,
    known_prefix: str | SIUnit,
    unknown_prefix: str | SIUnit,
) -> float:

    if isinstance(known_prefix, str):
        known_prefix = SIUnit[known_prefix.lower()]
    if isinstance(unknown_prefix, str):
        unknown_prefix = SIUnit[unknown_prefix.lower()]
    unknown_amount: float = known_amount * (
        10 ** (known_prefix.value - unknown_prefix.value)
    )
    return unknown_amount
