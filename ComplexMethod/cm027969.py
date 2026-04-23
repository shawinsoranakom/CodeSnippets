def convert_temperature(temperature: float, from_unit: str, to_unit: str) -> str:
    """Convert temperature between Celsius, Fahrenheit, and Kelvin"""
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()

    # Convert to Celsius first
    if from_unit == "fahrenheit" or from_unit == "f":
        celsius = (temperature - 32) * 5/9
    elif from_unit == "kelvin" or from_unit == "k":
        celsius = temperature - 273.15
    elif from_unit == "celsius" or from_unit == "c":
        celsius = temperature
    else:
        return "Error: Supported units are Celsius, Fahrenheit, and Kelvin"

    # Convert from Celsius to target unit
    if to_unit == "fahrenheit" or to_unit == "f":
        result = celsius * 9/5 + 32
        unit_symbol = "°F"
    elif to_unit == "kelvin" or to_unit == "k":
        result = celsius + 273.15
        unit_symbol = "K"
    elif to_unit == "celsius" or to_unit == "c":
        result = celsius
        unit_symbol = "°C"
    else:
        return "Error: Supported units are Celsius, Fahrenheit, and Kelvin"

    return f"{temperature}° {from_unit.title()} = {result:.2f}{unit_symbol}"