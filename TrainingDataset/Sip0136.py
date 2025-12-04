def find_previous_power_of_two(number: int) -> int:
    
    if not isinstance(number, int) or number < 0:
        raise ValueError("Input must be a non-negative integer")
    if number == 0:
        return 0
    power = 1
    while power <= number:
        power <<= 1  
    return power >> 1 if number > 1 else 1
