def hsv_to_rgb(hue: float, saturation: float, value: float) -> list[int]:
    """
    Conversion from the HSV-representation to the RGB-representation.
    Expected RGB-values taken from
    https://www.rapidtables.com/convert/color/hsv-to-rgb.html

    >>> hsv_to_rgb(0, 0, 0)
    [0, 0, 0]
    >>> hsv_to_rgb(0, 0, 1)
    [255, 255, 255]
    >>> hsv_to_rgb(0, 1, 1)
    [255, 0, 0]
    >>> hsv_to_rgb(60, 1, 1)
    [255, 255, 0]
    >>> hsv_to_rgb(120, 1, 1)
    [0, 255, 0]
    >>> hsv_to_rgb(240, 1, 1)
    [0, 0, 255]
    >>> hsv_to_rgb(300, 1, 1)
    [255, 0, 255]
    >>> hsv_to_rgb(180, 0.5, 0.5)
    [64, 128, 128]
    >>> hsv_to_rgb(234, 0.14, 0.88)
    [193, 196, 224]
    >>> hsv_to_rgb(330, 0.75, 0.5)
    [128, 32, 80]
    """
    if hue < 0 or hue > 360:
        raise Exception("hue should be between 0 and 360")

    if saturation < 0 or saturation > 1:
        raise Exception("saturation should be between 0 and 1")

    if value < 0 or value > 1:
        raise Exception("value should be between 0 and 1")

    chroma = value * saturation
    hue_section = hue / 60
    second_largest_component = chroma * (1 - abs(hue_section % 2 - 1))
    match_value = value - chroma

    if hue_section >= 0 and hue_section <= 1:
        red = round(255 * (chroma + match_value))
        green = round(255 * (second_largest_component + match_value))
        blue = round(255 * (match_value))
    elif hue_section > 1 and hue_section <= 2:
        red = round(255 * (second_largest_component + match_value))
        green = round(255 * (chroma + match_value))
        blue = round(255 * (match_value))
    elif hue_section > 2 and hue_section <= 3:
        red = round(255 * (match_value))
        green = round(255 * (chroma + match_value))
        blue = round(255 * (second_largest_component + match_value))
    elif hue_section > 3 and hue_section <= 4:
        red = round(255 * (match_value))
        green = round(255 * (second_largest_component + match_value))
        blue = round(255 * (chroma + match_value))
    elif hue_section > 4 and hue_section <= 5:
        red = round(255 * (second_largest_component + match_value))
        green = round(255 * (match_value))
        blue = round(255 * (chroma + match_value))
    else:
        red = round(255 * (chroma + match_value))
        green = round(255 * (match_value))
        blue = round(255 * (second_largest_component + match_value))

    return [red, green, blue]