def get_index_of_rightmost_set_bit(number: int) -> int:
   
    if not isinstance(number, int) or number < 0:
        raise ValueError("Input must be a non-negative integer")

    intermediate = number & ~(number - 1)
    index = 0
    while intermediate:
        intermediate >>= 1
        index += 1
    return index - 1

