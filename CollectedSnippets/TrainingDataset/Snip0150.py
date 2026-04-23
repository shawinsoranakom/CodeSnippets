def reverse_bit(number: int) -> int:
   
    if not isinstance(number, int):
        raise TypeError("Input value must be an 'int' type")
    if number < 0:
        raise ValueError("The value of input must be non-negative")

    result = 0
    for _ in range(32):
        result <<= 1
        end_bit = number & 1
        number >>= 1
        result |= end_bit
    return result
