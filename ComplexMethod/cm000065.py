def compute_nums(n: int) -> list[int]:
    """
    Returns a list of first n odd composite numbers which do
    not follow the conjecture.
    >>> compute_nums(1)
    [5777]
    >>> compute_nums(2)
    [5777, 5993]
    >>> compute_nums(0)
    Traceback (most recent call last):
        ...
    ValueError: n must be >= 0
    >>> compute_nums("a")
    Traceback (most recent call last):
        ...
    ValueError: n must be an integer
    >>> compute_nums(1.1)
    Traceback (most recent call last):
        ...
    ValueError: n must be an integer

    """
    if not isinstance(n, int):
        raise ValueError("n must be an integer")
    if n <= 0:
        raise ValueError("n must be >= 0")

    list_nums = []
    for num in range(len(odd_composites)):
        i = 0
        while 2 * i * i <= odd_composites[num]:
            rem = odd_composites[num] - 2 * i * i
            if is_prime(rem):
                break
            i += 1
        else:
            list_nums.append(odd_composites[num])
            if len(list_nums) == n:
                return list_nums

    return []