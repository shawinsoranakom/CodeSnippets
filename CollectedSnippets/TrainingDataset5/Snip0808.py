def couloumbs_law(
    force: float, charge1: float, charge2: float, distance: float
) -> dict[str, float]:

    charge_product = abs(charge1 * charge2)

    if (force, charge1, charge2, distance).count(0) != 1:
        raise ValueError("One and only one argument must be 0")
    if distance < 0:
        raise ValueError("Distance cannot be negative")
    if force == 0:
        force = COULOMBS_CONSTANT * charge_product / (distance**2)
        return {"force": force}
    elif charge1 == 0:
        charge1 = abs(force) * (distance**2) / (COULOMBS_CONSTANT * charge2)
        return {"charge1": charge1}
    elif charge2 == 0:
        charge2 = abs(force) * (distance**2) / (COULOMBS_CONSTANT * charge1)
        return {"charge2": charge2}
    elif distance == 0:
        distance = (COULOMBS_CONSTANT * charge_product / abs(force)) ** 0.5
        return {"distance": distance}
    raise ValueError("Exactly one argument must be 0")
