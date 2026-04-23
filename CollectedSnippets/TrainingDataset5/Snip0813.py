def get_significant_digits(colors: list) -> str:
    digit = ""
    for color in colors:
        if color not in significant_figures_color_values:
            msg = f"{color} is not a valid color for significant figure bands"
            raise ValueError(msg)
        digit = digit + str(significant_figures_color_values[color])
    return str(digit)
