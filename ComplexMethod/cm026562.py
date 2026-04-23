def _convert_color(color: tuple) -> RGBColorState:
    """Convert the given color to the reduced RGBColorState color.

    RGBColorStat contains only 8 colors including white and black,
    so a conversion is required.
    """
    if color is None:
        return RGBColorState.WHITE

    hue = int(color[0])
    saturation = int(color[1])
    if saturation < 5:
        return RGBColorState.WHITE
    if 30 < hue <= 90:
        return RGBColorState.YELLOW
    if 90 < hue <= 160:
        return RGBColorState.GREEN
    if 150 < hue <= 210:
        return RGBColorState.TURQUOISE
    if 210 < hue <= 270:
        return RGBColorState.BLUE
    if 270 < hue <= 330:
        return RGBColorState.PURPLE
    return RGBColorState.RED