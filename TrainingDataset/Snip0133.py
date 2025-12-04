def get_set_bits_count_using_modulo_operator(number: int) -> int:
  
    if number < 0:
        raise ValueError("the value of input must not be negative")
    result = 0
    while number:
        if number % 2 == 1:
            result += 1
        number >>= 1
    return result
