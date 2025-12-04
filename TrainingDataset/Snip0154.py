def is_bit_set(number: int, position: int) -> bool:

    return ((number >> position) & 1) == 1
