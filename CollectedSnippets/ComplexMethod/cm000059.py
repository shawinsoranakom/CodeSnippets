def casimir_force(force: float, area: float, distance: float) -> dict[str, float]:
    """
    Input Parameters
    ----------------
    force -> Casimir Force : magnitude in Newtons

    area -> Surface area of each plate : magnitude in square meters

    distance -> Distance between two plates : distance in Meters

    Returns
    -------
    result : dict name, value pair of the parameter having Zero as it's value

    Returns the value of one of the parameters specified as 0, provided the values of
    other parameters are given.
    >>> casimir_force(force = 0, area = 4, distance = 0.03)
    {'force': 6.4248189174864216e-21}

    >>> casimir_force(force = 2635e-13, area = 0.0023, distance = 0)
    {'distance': 1.0323056015031114e-05}

    >>> casimir_force(force = 2737e-21, area = 0, distance = 0.0023746)
    {'area': 0.06688838837354052}

    >>> casimir_force(force = 3457e-12, area = 0, distance = 0)
    Traceback (most recent call last):
        ...
    ValueError: One and only one argument must be 0

    >>> casimir_force(force = 3457e-12, area = 0, distance = -0.00344)
    Traceback (most recent call last):
        ...
    ValueError: Distance can not be negative

    >>> casimir_force(force = -912e-12, area = 0, distance = 0.09374)
    Traceback (most recent call last):
        ...
    ValueError: Magnitude of force can not be negative
    """

    if (force, area, distance).count(0) != 1:
        raise ValueError("One and only one argument must be 0")
    if force < 0:
        raise ValueError("Magnitude of force can not be negative")
    if distance < 0:
        raise ValueError("Distance can not be negative")
    if area < 0:
        raise ValueError("Area can not be negative")
    if force == 0:
        force = (REDUCED_PLANCK_CONSTANT * SPEED_OF_LIGHT * pi**2 * area) / (
            240 * (distance) ** 4
        )
        return {"force": force}
    elif area == 0:
        area = (240 * force * (distance) ** 4) / (
            REDUCED_PLANCK_CONSTANT * SPEED_OF_LIGHT * pi**2
        )
        return {"area": area}
    elif distance == 0:
        distance = (
            (REDUCED_PLANCK_CONSTANT * SPEED_OF_LIGHT * pi**2 * area) / (240 * force)
        ) ** (1 / 4)
        return {"distance": distance}
    raise ValueError("One and only one argument must be 0")