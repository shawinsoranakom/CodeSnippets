def intword(value):
    """
    Convert a large integer to a friendly text representation. Works best
    for numbers over 1 million. For example, 1000000 becomes '1.0 million',
    1200000 becomes '1.2 million' and '1200000000' becomes '1.2 billion'.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value

    abs_value = abs(value)
    if abs_value < 1000000:
        return value

    for exponent, converter in intword_converters:
        large_number = 10**exponent
        if abs_value < large_number * 1000:
            new_value = value / large_number
            rounded_value = round_away_from_one(new_value)
            return converter(abs(rounded_value)) % {
                "value": defaultfilters.floatformat(new_value, 1),
            }
    return value