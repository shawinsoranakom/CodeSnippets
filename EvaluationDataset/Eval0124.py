def fahrenheit_to_celsius(fahrenheit: float, ndigits: int = 2) -> float:
    return round((float(fahrenheit) - 32) * 5 / 9, ndigits)
