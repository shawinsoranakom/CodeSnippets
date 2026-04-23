def stringify_default(default: Any) -> str:
    """
    Returns the string representation of a default value, as used in docstring: numbers are left as is, all other
    objects are in backtiks.

    Args:
        default (`Any`): The default value to process

    Returns:
        `str`: The string representation of that default.
    """
    if isinstance(default, bool):
        # We need to test for bool first as a bool passes isinstance(xxx, (int, float))
        return f"`{default}`"
    elif isinstance(default, enum.Enum):
        # We need to test for enum first as an enum with int values will pass isinstance(xxx, (int, float))
        return f"`{str(default)}`"
    elif isinstance(default, int):
        return str(default)
    elif isinstance(default, float):
        result = str(default)
        return str(round(default, 2)) if len(result) > 6 else result
    elif isinstance(default, str):
        return str(default) if default.isnumeric() else f'`"{default}"`'
    elif isinstance(default, type):
        return f"`{default.__name__}`"
    else:
        return f"`{default}`"