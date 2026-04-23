def bitwise_addition_recursive(number: int, other_number: int) -> int:

    if not isinstance(number, int) or not isinstance(other_number, int):
        raise TypeError("Both arguments MUST be integers!")

    if number < 0 or other_number < 0:
        raise ValueError("Both arguments MUST be non-negative!")

    bitwise_sum = number ^ other_number
    carry = number & other_number

    if carry == 0:
        return bitwise_sum

    return bitwise_addition_recursive(bitwise_sum, carry << 1)
