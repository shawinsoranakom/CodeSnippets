def celsius_to_rankine(celsius: float, ndigits: int = 2) -> float:

    return round((float(celsius) * 9 / 5) + 491.67, ndigits)
