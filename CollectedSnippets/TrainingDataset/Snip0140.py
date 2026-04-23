def get_highest_set_bit_position(number: int) -> int:
    if not isinstance(number, int):
        raise TypeError("Input value must be an 'int' type")

    position = 0
    while number:
        position += 1
        number >>= 1

    return position

