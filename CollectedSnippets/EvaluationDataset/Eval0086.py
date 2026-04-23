def decimal_to_any(num: int, base: int) -> str:

    if isinstance(num, float):
        raise TypeError("int() can't convert non-string with explicit base")
    if num < 0:
        raise ValueError("parameter must be positive int")
    if isinstance(base, str):
        raise TypeError("'str' object cannot be interpreted as an integer")
    if isinstance(base, float):
        raise TypeError("'float' object cannot be interpreted as an integer")
    if base in (0, 1):
        raise ValueError("base must be >= 2")
    if base > 36:
        raise ValueError("base must be <= 36")
    new_value = ""
    mod = 0
    div = 0
    while div != 1:
        div, mod = divmod(num, base)
        if base >= 11 and 9 < mod < 36:
            actual_value = ALPHABET_VALUES[str(mod)]
        else:
            actual_value = str(mod)
        new_value += actual_value
        div = num // base
        num = div
        if div == 0:
            return str(new_value[::-1])
        elif div == 1:
            new_value += str(div)
            return str(new_value[::-1])

    return new_value[::-1]
