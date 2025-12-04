def get_bit(number: int, position: int) -> int:

    return int((number & (1 << position)) != 0)
