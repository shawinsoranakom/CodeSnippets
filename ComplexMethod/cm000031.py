def sieve_er(n):
    """
    input: positive integer 'N' > 2
    returns a list of prime numbers from 2 up to N.

    This function implements the algorithm called
    sieve of erathostenes.

    >>> sieve_er(8)
    [2, 3, 5, 7]
    >>> sieve_er(-1)
    Traceback (most recent call last):
        ...
    AssertionError: 'N' must been an int and > 2
    >>> sieve_er("test")
    Traceback (most recent call last):
        ...
    AssertionError: 'N' must been an int and > 2
    """

    # precondition
    assert isinstance(n, int) and (n > 2), "'N' must been an int and > 2"

    # beginList: contains all natural numbers from 2 up to N
    begin_list = list(range(2, n + 1))

    ans = []  # this list will be returns.

    # actual sieve of erathostenes
    for i in range(len(begin_list)):
        for j in range(i + 1, len(begin_list)):
            if (begin_list[i] != 0) and (begin_list[j] % begin_list[i] == 0):
                begin_list[j] = 0

    # filters actual prime numbers.
    ans = [x for x in begin_list if x != 0]

    # precondition
    assert isinstance(ans, list), "'ans' must been from type list"

    return ans