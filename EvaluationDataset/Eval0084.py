def convert_small_number(num: int) -> str:

    if num < 0:
        raise ValueError("This function only accepts non-negative integers")
    if num >= 100:
        raise ValueError("This function only converts numbers less than 100")
    tens, ones = divmod(num, 10)
    if tens == 0:
        return NumberWords.ONES.value[ones] or "zero"
    if tens == 1:
        return NumberWords.TEENS.value[ones]
    return (
        NumberWords.TENS.value[tens]
        + ("-" if NumberWords.ONES.value[ones] else "")
        + NumberWords.ONES.value[ones]
    )
