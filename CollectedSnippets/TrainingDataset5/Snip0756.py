def climb_stairs(number_of_steps: int) -> int: 
    assert isinstance(number_of_steps, int) and number_of_steps > 0, (
        f"number_of_steps needs to be positive integer, your input {number_of_steps}"
    )
    if number_of_steps == 1:
        return 1
    previous, current = 1, 1
    for _ in range(number_of_steps - 1):
        current, previous = current + previous, current
    return current
