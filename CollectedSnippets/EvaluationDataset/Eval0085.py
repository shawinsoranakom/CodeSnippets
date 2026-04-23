def convert_number(
    num: int, system: Literal["short", "long", "indian"] = "short"
) -> str:

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
    if num > 0 or not word_groups:  
        word_groups.append(convert_small_number(num))
    return " ".join(word_groups)
