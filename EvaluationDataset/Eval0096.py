def hex_to_decimal(hex_string: str) -> int:

    hex_string = hex_string.strip().lower()
    if not hex_string:
        raise ValueError("Empty string was passed to the function")
    is_negative = hex_string[0] == "-"
    if is_negative:
        hex_string = hex_string[1:]
    if not all(char in hex_table for char in hex_string):
        raise ValueError("Non-hexadecimal value was passed to the function")
    decimal_number = 0
    for char in hex_string:
        decimal_number = 16 * decimal_number + hex_table[char]
    return -decimal_number if is_negative else decimal_number
