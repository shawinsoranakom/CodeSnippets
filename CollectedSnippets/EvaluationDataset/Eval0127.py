def kelvin_to_celsius(kelvin: float, ndigits: int = 2) -> float:
    return round(float(kelvin) - 273.15, ndigits)
