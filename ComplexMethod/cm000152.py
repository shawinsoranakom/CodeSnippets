def miller_rabin(n: int, allow_probable: bool = False) -> bool:
    """Deterministic Miller-Rabin algorithm for primes ~< 3.32e24.

    Uses numerical analysis results to return whether or not the passed number
    is prime. If the passed number is above the upper limit, and
    allow_probable is True, then a return value of True indicates that n is
    probably prime. This test does not allow False negatives- a return value
    of False is ALWAYS composite.

    Parameters
    ----------
    n : int
        The integer to be tested. Since we usually care if a number is prime,
        n < 2 returns False instead of raising a ValueError.
    allow_probable: bool, default False
        Whether or not to test n above the upper bound of the deterministic test.

    Raises
    ------
    ValueError

    Reference
    ---------
    https://en.wikipedia.org/wiki/Miller%E2%80%93Rabin_primality_test
    """
    if n == 2:
        return True
    if not n % 2 or n < 2:
        return False
    if n > 5 and n % 10 not in (1, 3, 7, 9):  # can quickly check last digit
        return False
    if n > 3_317_044_064_679_887_385_961_981 and not allow_probable:
        raise ValueError(
            "Warning: upper bound of deterministic test is exceeded. "
            "Pass allow_probable=True to allow probabilistic test. "
            "A return value of True indicates a probable prime."
        )
    # array bounds provided by analysis
    bounds = [
        2_047,
        1_373_653,
        25_326_001,
        3_215_031_751,
        2_152_302_898_747,
        3_474_749_660_383,
        341_550_071_728_321,
        1,
        3_825_123_056_546_413_051,
        1,
        1,
        318_665_857_834_031_151_167_461,
        3_317_044_064_679_887_385_961_981,
    ]

    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]
    for idx, _p in enumerate(bounds, 1):
        if n < _p:
            # then we have our last prime to check
            plist = primes[:idx]
            break
    d, s = n - 1, 0
    # break up n -1 into a power of 2 (s) and
    # remaining odd component
    # essentially, solve for d * 2 ** s == n - 1
    while d % 2 == 0:
        d //= 2
        s += 1
    for prime in plist:
        pr = False
        for r in range(s):
            m = pow(prime, d * 2**r, n)
            # see article for analysis explanation for m
            if (r == 0 and m == 1) or ((m + 1) % n == 0):
                pr = True
                # this loop will not determine compositeness
                break
        if pr:
            continue
        # if pr is False, then the above loop never evaluated to true,
        # and the n MUST be composite
        return False
    return True