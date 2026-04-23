def convert_number(
    num: int, system: Literal["short", "long", "indian"] = "short"
) -> str:
    """
    Converts an integer to English words.

    :param num: The integer to be converted
    :param system: The numbering system (short, long, or Indian)

    >>> convert_number(0)
    'zero'
    >>> convert_number(1)
    'one'
    >>> convert_number(100)
    'one hundred'
    >>> convert_number(-100)
    'negative one hundred'
    >>> convert_number(123_456_789_012_345) # doctest: +NORMALIZE_WHITESPACE
    'one hundred twenty-three trillion four hundred fifty-six billion
    seven hundred eighty-nine million twelve thousand three hundred forty-five'
    >>> convert_number(123_456_789_012_345, "long") # doctest: +NORMALIZE_WHITESPACE
    'one hundred twenty-three thousand four hundred fifty-six milliard
    seven hundred eighty-nine million twelve thousand three hundred forty-five'
    >>> convert_number(12_34_56_78_90_12_345, "indian") # doctest: +NORMALIZE_WHITESPACE
    'one crore crore twenty-three lakh crore
    forty-five thousand six hundred seventy-eight crore
    ninety lakh twelve thousand three hundred forty-five'
    >>> convert_number(10**18)
    Traceback (most recent call last):
    ...
    ValueError: Input number is too large
    >>> convert_number(10**21, "long")
    Traceback (most recent call last):
    ...
    ValueError: Input number is too large
    >>> convert_number(10**19, "indian")
    Traceback (most recent call last):
    ...
    ValueError: Input number is too large
    """
    word_groups = []

    if num < 0:
        word_groups.append("negative")
        num *= -1

    if num > NumberingSystem.max_value(system):
        raise ValueError("Input number is too large")

    for power, unit in NumberingSystem[system.upper()].value:
        digit_group, num = divmod(num, 10**power)
        if digit_group > 0:
            word_group = (
                convert_number(digit_group, system)
                if digit_group >= 100
                else convert_small_number(digit_group)
            )
            word_groups.append(f"{word_group} {unit}")
    if num > 0 or not word_groups:  # word_groups is only empty if input num was 0
        word_groups.append(convert_small_number(num))
    return " ".join(word_groups)