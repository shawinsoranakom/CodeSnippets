def find_narcissistic_numbers(limit: int) -> list[int]:
    if limit <= 0:
        return []

    narcissistic_nums = []

    power_cache: dict[tuple[int, int], int] = {}

    def get_digit_power(digit: int, power: int) -> int:
        if (power, digit) not in power_cache:
            power_cache[(power, digit)] = digit**power
        return power_cache[(power, digit)]

    for number in range(limit):
        num_digits = len(str(number))

        remaining = number
        digit_sum = 0
        while remaining > 0:
            digit = remaining % 10
            digit_sum += get_digit_power(digit, num_digits)
            remaining //= 10

        if digit_sum == number:
            narcissistic_nums.append(number)

    return narcissistic_nums
