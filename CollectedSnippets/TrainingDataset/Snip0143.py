def is_power_of_two(number: int) -> bool:
  
    if number < 0:
        raise ValueError("number must not be negative")
    return number & (number - 1) == 0
