def prime_factorization(number):
    """
    input: positive integer 'number'
    returns a list of the prime number factors of 'number'

    >>> prime_factorization(0)
    [0]
    >>> prime_factorization(8)
    [2, 2, 2]
    >>> prime_factorization(287)
    [7, 41]
    >>> prime_factorization(-1)
    Traceback (most recent call last):
        ...
    AssertionError: 'number' must been an int and >= 0
    >>> prime_factorization("test")
    Traceback (most recent call last):
        ...
    AssertionError: 'number' must been an int and >= 0
    """

    # precondition
    assert isinstance(number, int) and number >= 0, "'number' must been an int and >= 0"

    ans = []  # this list will be returns of the function.

    # potential prime number factors.

    factor = 2

    quotient = number

    if number in {0, 1}:
        ans.append(number)

    # if 'number' not prime then builds the prime factorization of 'number'
    elif not is_prime(number):
        while quotient != 1:
            if is_prime(factor) and (quotient % factor == 0):
                ans.append(factor)
                quotient /= factor
            else:
                factor += 1

    else:
        ans.append(number)

    # precondition
    assert isinstance(ans, list), "'ans' must been from type list"

    return ans