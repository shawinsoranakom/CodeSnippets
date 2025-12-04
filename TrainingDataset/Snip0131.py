def get_1s_count(number: int) -> int:
  
    if not isinstance(number, int) or number < 0:
        raise ValueError("Input must be a non-negative integer")

    count = 0
    while number:
        
        number &= number - 1
        count += 1
    return count
