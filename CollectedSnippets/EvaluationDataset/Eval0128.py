def kelvin_to_fahrenheit(kelvin: float, ndigits: int = 2) -> float:
    return round(((float(kelvin) - 273.15) * 9 / 5) + 32, ndigits)
