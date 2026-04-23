def naturaltime(value):
    """
    For date and time values show how many seconds, minutes, or hours ago
    compared to current timestamp return representing string.
    """
    return NaturalTimeFormatter.string_for(value)