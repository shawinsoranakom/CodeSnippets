def get_reverse_bit_string(number: int) -> str:
    if not isinstance(number, int):
        msg = (
            "operation can not be conducted on an object of type "
            f"{type(number).__name__}"
        )
        raise TypeError(msg)
    bit_string = ""
    for _ in range(32):
        bit_string += str(number % 2)
        number >>= 1
    return bit_string
