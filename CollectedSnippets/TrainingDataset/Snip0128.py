def twos_complement(number: int) -> str:
  
    if number > 0:
        raise ValueError("input must be a negative integer")
    binary_number_length = len(bin(number)[3:])
    twos_complement_number = bin(abs(number) - (1 << binary_number_length))[3:]
    twos_complement_number = (
        (
            "1"
            + "0" * (binary_number_length - len(twos_complement_number))
            + twos_complement_number
        )
        if number < 0
        else "0"
    )
    return "0b" + twos_complement_number

