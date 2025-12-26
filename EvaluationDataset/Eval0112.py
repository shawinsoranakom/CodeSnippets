def pressure_conversion(value: float, from_type: str, to_type: str) -> float:

    if from_type not in PRESSURE_CONVERSION:
        raise ValueError(
            f"Invalid 'from_type' value: {from_type!r}  Supported values are:\n"
            + ", ".join(PRESSURE_CONVERSION)
        )
    if to_type not in PRESSURE_CONVERSION:
        raise ValueError(
            f"Invalid 'to_type' value: {to_type!r}.  Supported values are:\n"
            + ", ".join(PRESSURE_CONVERSION)
        )
    return (
        value
        * PRESSURE_CONVERSION[from_type].from_factor
        * PRESSURE_CONVERSION[to_type].to_factor
    )

