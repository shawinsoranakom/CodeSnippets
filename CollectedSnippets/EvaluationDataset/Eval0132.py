def weight_conversion(from_type: str, to_type: str, value: float) -> float:

    if to_type not in KILOGRAM_CHART or from_type not in WEIGHT_TYPE_CHART:
        msg = (
            f"Invalid 'from_type' or 'to_type' value: {from_type!r}, {to_type!r}\n"
            f"Supported values are: {', '.join(WEIGHT_TYPE_CHART)}"
        )
        raise ValueError(msg)
    return value * KILOGRAM_CHART[to_type] * WEIGHT_TYPE_CHART[from_type]
