def get_set_bits_count_using_brian_kernighans_algorithm(number: int) -> int:
  
    if number < 0:
        raise ValueError("the value of input must not be negative")
    result = 0
    while number:
        number &= number - 1
        result += 1
    return result
