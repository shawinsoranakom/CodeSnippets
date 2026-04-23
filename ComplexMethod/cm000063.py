def solution(limit: int = 1000000) -> int:
    """
    returns the values of n less than or equal to the limit
    have exactly ten distinct solutions.
    >>> solution(100)
    0
    >>> solution(10000)
    45
    >>> solution(50050)
    292
    """
    limit = limit + 1
    frequency = [0] * limit
    for first_term in range(1, limit):
        for n in range(first_term, limit, first_term):
            common_difference = first_term + n / first_term
            if common_difference % 4:  # d must be divisible by 4
                continue
            else:
                common_difference /= 4
                if (
                    first_term > common_difference
                    and first_term < 4 * common_difference
                ):  # since x, y, z are positive integers
                    frequency[n] += 1  # so z > 0, a > d and 4d < a

    count = sum(1 for x in frequency[1:limit] if x == 10)

    return count