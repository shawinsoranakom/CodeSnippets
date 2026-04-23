def unit_multiplier(unit: str) -> int:  # pylint: disable=R0911
    """Return the multiplier for a given unit measurement."""
    if unit == "thousands":
        return 1000
    if unit in ["tens of thousands", "tens thousands"]:
        return 10000
    if unit in ["hundreds of thousands", "hundreds thousands"]:
        return 100000
    if unit in ["millions", "milions"]:
        return 1000000
    if unit in ["tens of millions", "tens millions"]:
        return 10000000
    if unit in ["hundreds of millions", "hundreds millions"]:
        return 100000000
    if unit == "billions":
        return 1000000000
    if unit == "trillions":
        return 1000000000000
    return 1