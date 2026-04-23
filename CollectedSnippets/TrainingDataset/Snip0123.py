def binary_count_trailing_zeros(a: int) -> int:
  
    if a < 0:
        raise ValueError("Input value must be a positive integer")
    elif isinstance(a, float):
        raise TypeError("Input value must be a 'int' type")
    return 0 if (a == 0) else int(log2(a & -a))
