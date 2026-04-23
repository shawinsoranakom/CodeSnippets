def slow_primes(max_n: int) -> Generator[int]:
    """
    Return a list of all primes numbers up to max.
    >>> list(slow_primes(0))
    []
    >>> list(slow_primes(-1))
    []
    >>> list(slow_primes(-10))
    []
    >>> list(slow_primes(25))
    [2, 3, 5, 7, 11, 13, 17, 19, 23]
    >>> list(slow_primes(11))
    [2, 3, 5, 7, 11]
    >>> list(slow_primes(33))
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
    >>> list(slow_primes(1000))[-1]
    997
    """
    numbers: Generator = (i for i in range(1, (max_n + 1)))
    for i in (n for n in numbers if n > 1):
        for j in range(2, i):
            if (i % j) == 0:
                break
        else:
            yield i