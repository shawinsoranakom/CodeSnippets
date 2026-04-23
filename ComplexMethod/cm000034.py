def kg_v(number1, number2):
    """
    Least common multiple
    input: two positive integer 'number1' and 'number2'
    returns the least common multiple of 'number1' and 'number2'

    >>> kg_v(8,10)
    40
    >>> kg_v(824,67)
    55208
    >>> kg_v(1, 10)
    10
    >>> kg_v(0)
    Traceback (most recent call last):
        ...
    TypeError: kg_v() missing 1 required positional argument: 'number2'
    >>> kg_v(10,-1)
    Traceback (most recent call last):
        ...
    AssertionError: 'number1' and 'number2' must been positive integer.
    >>> kg_v("test","test2")
    Traceback (most recent call last):
        ...
    AssertionError: 'number1' and 'number2' must been positive integer.
    """

    # precondition
    assert (
        isinstance(number1, int)
        and isinstance(number2, int)
        and (number1 >= 1)
        and (number2 >= 1)
    ), "'number1' and 'number2' must been positive integer."

    ans = 1  # actual answer that will be return.

    # for kgV (x,1)
    if number1 > 1 and number2 > 1:
        # builds the prime factorization of 'number1' and 'number2'
        prime_fac_1 = prime_factorization(number1)
        prime_fac_2 = prime_factorization(number2)

    elif number1 == 1 or number2 == 1:
        prime_fac_1 = []
        prime_fac_2 = []
        ans = max(number1, number2)

    count1 = 0
    count2 = 0

    done = []  # captured numbers int both 'primeFac1' and 'primeFac2'

    # iterates through primeFac1
    for n in prime_fac_1:
        if n not in done:
            if n in prime_fac_2:
                count1 = prime_fac_1.count(n)
                count2 = prime_fac_2.count(n)

                for _ in range(max(count1, count2)):
                    ans *= n

            else:
                count1 = prime_fac_1.count(n)

                for _ in range(count1):
                    ans *= n

            done.append(n)

    # iterates through primeFac2
    for n in prime_fac_2:
        if n not in done:
            count2 = prime_fac_2.count(n)

            for _ in range(count2):
                ans *= n

            done.append(n)

    # precondition
    assert isinstance(ans, int) and (ans >= 0), (
        "'ans' must been from type int and positive"
    )

    return ans