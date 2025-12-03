def backtrack(
    needed_sum: int,
    power: int,
    current_number: int,
    current_sum: int,
    solutions_count: int,
) -> tuple[int, int]:
    if current_sum == needed_sum:
        solutions_count += 1
        return current_sum, solutions_count

    i_to_n = current_number**power
    if current_sum + i_to_n <= needed_sum:
        current_sum += i_to_n
        current_sum, solutions_count = backtrack(
            needed_sum, power, current_number + 1, current_sum, solutions_count
        )
        current_sum -= i_to_n
    if i_to_n < needed_sum:
        current_sum, solutions_count = backtrack(
            needed_sum, power, current_number + 1, current_sum, solutions_count
        )
    return current_sum, solutions_count
