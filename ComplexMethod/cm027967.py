def convert_temperature(temperature: float, from_unit: str, to_unit: str) -> Dict[str, Union[float, str, Dict]]:
    """
    Convert temperature between Celsius, Fahrenheit, and Kelvin.

    Use this function when users ask to convert temperatures between
    different units (C, F, K).

    Args:
        temperature: Temperature value to convert
        from_unit: Source unit ('C', 'F', 'K')
        to_unit: Target unit ('C', 'F', 'K')

    Returns:
        Dictionary with conversion results
    """
    try:
        # Normalize unit inputs
        from_unit = from_unit.upper()
        to_unit = to_unit.upper()

        # Validate units
        valid_units = ['C', 'F', 'K']
        if from_unit not in valid_units or to_unit not in valid_units:
            return {
                "error": f"Invalid units. Use C, F, or K. Got: {from_unit} to {to_unit}",
                "status": "error"
            }

        # Convert to Celsius first
        if from_unit == 'F':
            celsius = (temperature - 32) * 5/9
        elif from_unit == 'K':
            celsius = temperature - 273.15
        else:
            celsius = temperature

        # Convert from Celsius to target unit
        if to_unit == 'F':
            result = celsius * 9/5 + 32
        elif to_unit == 'K':
            result = celsius + 273.15
        else:
            result = celsius

        return {
            "result": round(result, 2),
            "conversion": {
                "from": {"value": temperature, "unit": from_unit},
                "to": {"value": round(result, 2), "unit": to_unit}
            },
            "status": "success"
        }
    except Exception as e:
        return {
            "error": f"Error converting temperature: {str(e)}",
            "status": "error"
        }