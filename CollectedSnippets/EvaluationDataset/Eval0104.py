def octal_to_binary(octal_number: str) -> str:

    if not octal_number:
        raise ValueError("Empty string was passed to the function")

    binary_number = ""
    octal_digits = "01234567"
    for digit in octal_number:
        if digit not in octal_digits:
            raise ValueError("Non-octal value was passed to the function")

        binary_digit = ""
        value = int(digit)
        for _ in range(3):
            binary_digit = str(value % 2) + binary_digit
            value //= 2
        binary_number += binary_digit

    return binary_numbe
