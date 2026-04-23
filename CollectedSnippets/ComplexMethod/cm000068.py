def check(number: int) -> bool:
    """
    Takes a number and checks if it is pandigital both from start and end


    >>> check(123456789987654321)
    True

    >>> check(120000987654321)
    False

    >>> check(1234567895765677987654321)
    True

    """

    check_last = [0] * 11
    check_front = [0] * 11

    # mark last 9 numbers
    for _ in range(9):
        check_last[int(number % 10)] = 1
        number = number // 10
    # flag
    f = True

    # check last 9 numbers for pandigitality

    for x in range(9):
        if not check_last[x + 1]:
            f = False
    if not f:
        return f

    # mark first 9 numbers
    number = int(str(number)[:9])

    for _ in range(9):
        check_front[int(number % 10)] = 1
        number = number // 10

    # check first 9 numbers for pandigitality

    for x in range(9):
        if not check_front[x + 1]:
            f = False
    return f