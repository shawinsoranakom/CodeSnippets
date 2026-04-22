def simplify_number(num: int) -> str:
    """Simplifies number into Human readable format, returns str"""
    num_converted = float("{:.2g}".format(num))
    magnitude = 0
    while abs(num_converted) >= 1000:
        magnitude += 1
        num_converted /= 1000.0
    return "{}{}".format(
        "{:f}".format(num_converted).rstrip("0").rstrip("."),
        ["", "k", "m", "b", "t"][magnitude],
    )