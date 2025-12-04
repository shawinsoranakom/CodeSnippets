def find_unique_number(arr: list[int]) -> int:
    
    if not arr:
        raise ValueError("input list must not be empty")
    if not all(isinstance(x, int) for x in arr):
        raise TypeError("all elements must be integers")

    result = 0
    for num in arr:
        result ^= num
    return result

