def color_xy_brightness_to_RGB(
    vX: float, vY: float, ibrightness: int, Gamut: GamutType | None = None
) -> tuple[int, int, int]:
    """Convert from XYZ to RGB."""
    if Gamut and not check_point_in_lamps_reach((vX, vY), Gamut):
        xy_closest = get_closest_point_to_point((vX, vY), Gamut)
        vX = xy_closest[0]
        vY = xy_closest[1]

    brightness = ibrightness / 255.0
    if brightness == 0.0:
        return (0, 0, 0)

    Y = brightness

    if vY == 0.0:
        vY += 1e-11

    X = (Y / vY) * vX
    Z = (Y / vY) * (1 - vX - vY)

    # Convert to RGB using Wide RGB D65 conversion.
    r = X * 1.656492 - Y * 0.354851 - Z * 0.255038
    g = -X * 0.707196 + Y * 1.655397 + Z * 0.036152
    b = X * 0.051713 - Y * 0.121364 + Z * 1.011530

    # Apply reverse gamma correction.
    r, g, b = (
        12.92 * x if (x <= 0.0031308) else ((1.0 + 0.055) * pow(x, (1.0 / 2.4)) - 0.055)
        for x in (r, g, b)
    )

    # Bring all negative components to zero.
    r, g, b = (max(0, x) for x in (r, g, b))

    # If one component is greater than 1, weight components by that value.
    max_component = max(r, g, b)
    if max_component > 1:
        r, g, b = (x / max_component for x in (r, g, b))

    ir, ig, ib = (int(x * 255) for x in (r, g, b))

    return (ir, ig, ib)