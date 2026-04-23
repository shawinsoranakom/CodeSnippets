def decimal_to_binary_iterative(num: int) -> str:
    """
    Convert an Integer Decimal Number to a Binary Number as str.
    >>> decimal_to_binary_iterative(0)
    '0b0'
    >>> decimal_to_binary_iterative(2)
    '0b10'
    >>> decimal_to_binary_iterative(7)
    '0b111'
    >>> decimal_to_binary_iterative(35)
    '0b100011'
    >>> # negatives work too
    >>> decimal_to_binary_iterative(-2)
    '-0b10'
    >>> # other floats will error
    >>> decimal_to_binary_iterative(16.16) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    TypeError: 'float' object cannot be interpreted as an integer
    >>> # strings will error as well
    >>> decimal_to_binary_iterative('0xfffff') # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    TypeError: 'str' object cannot be interpreted as an integer
    """

    if isinstance(num, float):
        raise TypeError("'float' object cannot be interpreted as an integer")
    if isinstance(num, str):
        raise TypeError("'str' object cannot be interpreted as an integer")

    if num == 0:
        return "0b0"

    negative = False

    if num < 0:
        negative = True
        num = -num

    binary: list[int] = []
    while num > 0:
        binary.insert(0, num % 2)
        num >>= 1

    if negative:
        return "-0b" + "".join(str(e) for e in binary)

    return "0b" + "".join(str(e) for e in binary)