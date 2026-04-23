def check_valid_gamut(Gamut: GamutType) -> bool:
    """Check if the supplied gamut is valid."""
    # Check if the three points of the supplied gamut are not on the same line.
    v1 = XYPoint(Gamut.green.x - Gamut.red.x, Gamut.green.y - Gamut.red.y)
    v2 = XYPoint(Gamut.blue.x - Gamut.red.x, Gamut.blue.y - Gamut.red.y)
    not_on_line = cross_product(v1, v2) > 0.0001

    # Check if all six coordinates of the gamut lie between 0 and 1.
    red_valid = (
        Gamut.red.x >= 0 and Gamut.red.x <= 1 and Gamut.red.y >= 0 and Gamut.red.y <= 1
    )
    green_valid = (
        Gamut.green.x >= 0
        and Gamut.green.x <= 1
        and Gamut.green.y >= 0
        and Gamut.green.y <= 1
    )
    blue_valid = (
        Gamut.blue.x >= 0
        and Gamut.blue.x <= 1
        and Gamut.blue.y >= 0
        and Gamut.blue.y <= 1
    )

    return not_on_line and red_valid and green_valid and blue_valid