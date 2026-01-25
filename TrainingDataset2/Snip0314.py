def is_prime(number: int) -> bool:
    assert isinstance(number, int) and (number >= 0), (
        "'number' must been an int and positive"
    )

    if 1 < number < 4:
        return True
    elif number < 2 or not number % 2:
        return False

    odd_numbers = range(3, int(math.sqrt(number) + 1), 2)
    return not any(not number % i for i in odd_numbers)
