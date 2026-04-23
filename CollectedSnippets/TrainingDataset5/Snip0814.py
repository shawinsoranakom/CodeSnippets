def check_validity(number_of_bands: int, colors: list) -> bool:
    if number_of_bands >= 3 and number_of_bands <= 6:
        if number_of_bands == len(colors):
            for color in colors:
                if color not in valid_colors:
                    msg = f"{color} is not a valid color"
                    raise ValueError(msg)
            return True
        else:
            msg = f"Expecting {number_of_bands} colors, provided {len(colors)} colors"
            raise ValueError(msg)
    else:
        msg = "Invalid number of bands. Resistor bands must be 3 to 6"
        raise ValueError(msg)
