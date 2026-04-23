def goldbach(number):
    """
    Goldbach's assumption
    input: a even positive integer 'number' > 2
    returns a list of two prime numbers whose sum is equal to 'number'

    >>> goldbach(8)
    [3, 5]
    >>> goldbach(824)
    [3, 821]
    >>> goldbach(0)
    Traceback (most recent call last):
        ...
    AssertionError: 'number' must been an int, even and > 2
    >>> goldbach(-1)
    Traceback (most recent call last):
        ...
    AssertionError: 'number' must been an int, even and > 2
    >>> goldbach("test")
    Traceback (most recent call last):
        ...
    AssertionError: 'number' must been an int, even and > 2
    """

    # precondition
    assert isinstance(number, int) and (number > 2) and is_even(number), (
        "'number' must been an int, even and > 2"
    )

    ans = []  # this list will returned

    # creates a list of prime numbers between 2 up to 'number'
    prime_numbers = get_prime_numbers(number)
    len_pn = len(prime_numbers)

    # run variable for while-loops.
    i = 0
    j = None

    # exit variable. for break up the loops
    loop = True

    while i < len_pn and loop:
        j = i + 1

        while j < len_pn and loop:
            if prime_numbers[i] + prime_numbers[j] == number:
                loop = False
                ans.append(prime_numbers[i])
                ans.append(prime_numbers[j])

            j += 1

        i += 1

    # precondition
    assert (
        isinstance(ans, list)
        and (len(ans) == 2)
        and (ans[0] + ans[1] == number)
        and is_prime(ans[0])
        and is_prime(ans[1])
    ), "'ans' must contains two primes. And sum of elements must been eq 'number'"

    return ans