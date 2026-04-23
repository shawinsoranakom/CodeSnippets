def convert_binary_prefix(
    known_amount: float,
    known_prefix: str | BinaryUnit,
    unknown_prefix: str | BinaryUnit,
) -> float:

    if isinstance(known_prefix, str):
        known_prefix = BinaryUnit[known_prefix.lower()]
    if isinstance(unknown_prefix, str):
        unknown_prefix = BinaryUnit[unknown_prefix.lower()]
    unknown_amount: float = known_amount * (
        2 ** ((known_prefix.value - unknown_prefix.value) * 10)
    )
    return unknown_amount

