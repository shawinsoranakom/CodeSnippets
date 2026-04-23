def fahrenheit_to_kelvin(fahrenheit: float, ndigits: int = 2) -> float:
    return round(((float(fahrenheit) - 32) * 5 / 9) + 273.15, ndigits)
