def energy_conversion(from_type: str, to_type: str, value: float) -> float:

    if to_type not in ENERGY_CONVERSION or from_type not in ENERGY_CONVERSION:
        msg = (
            f"Incorrect 'from_type' or 'to_type' value: {from_type!r}, {to_type!r}\n"
            f"Valid values are: {', '.join(ENERGY_CONVERSION)}"
        )
        raise ValueError(msg)
    return value * ENERGY_CONVERSION[from_type] / ENERGY_CONVERSION[to_type]
