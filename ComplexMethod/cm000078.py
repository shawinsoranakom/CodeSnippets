def slow_reversible_numbers(
    remaining_length: int, remainder: int, digits: list[int], length: int
) -> int:
    """
    Count the number of reversible numbers of given length.
    Iterate over possible digits considering parity of current sum remainder.
    >>> slow_reversible_numbers(1, 0, [0], 1)
    0
    >>> slow_reversible_numbers(2, 0, [0] * 2, 2)
    20
    >>> slow_reversible_numbers(3, 0, [0] * 3, 3)
    100
    """
    if remaining_length == 0:
        if digits[0] == 0 or digits[-1] == 0:
            return 0

        for i in range(length // 2 - 1, -1, -1):
            remainder += digits[i] + digits[length - i - 1]

            if remainder % 2 == 0:
                return 0

            remainder //= 10

        return 1

    if remaining_length == 1:
        if remainder % 2 == 0:
            return 0

        result = 0
        for digit in range(10):
            digits[length // 2] = digit
            result += slow_reversible_numbers(
                0, (remainder + 2 * digit) // 10, digits, length
            )
        return result

    result = 0
    for digit1 in range(10):
        digits[(length + remaining_length) // 2 - 1] = digit1

        if (remainder + digit1) % 2 == 0:
            other_parity_digits = ODD_DIGITS
        else:
            other_parity_digits = EVEN_DIGITS

        for digit2 in other_parity_digits:
            digits[(length - remaining_length) // 2] = digit2
            result += slow_reversible_numbers(
                remaining_length - 2,
                (remainder + digit1 + digit2) // 10,
                digits,
                length,
            )
    return result