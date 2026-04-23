def is_prime(number: int) -> bool:
    """Checks to see if a number is a prime in O(sqrt(n)).
    A number is prime if it has exactly two factors: 1 and itself.
    Returns boolean representing primality of given number (i.e., if the
    result is true, then the number is indeed prime else it is not).

    >>> is_prime(2)
    True
    >>> is_prime(3)
    True
    >>> is_prime(27)
    False
    >>> is_prime(2999)
    True
    >>> is_prime(0)
    False
    >>> is_prime(1)
    False
    """

    if 1 < number < 4:
        # 2 and 3 are primes
        return True
    elif number < 2 or number % 2 == 0 or number % 3 == 0:
        # Negatives, 0, 1, all even numbers, all multiples of 3 are not primes
        return False

    # All primes number are in format of 6k +/- 1
    for i in range(5, int(math.sqrt(number) + 1), 6):
        if number % i == 0 or number % (i + 2) == 0:
            return False
    return True