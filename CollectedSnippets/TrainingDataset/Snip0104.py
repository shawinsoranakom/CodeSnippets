def solve(needed_sum: int, power: int) -> int:
    if not (1 <= needed_sum <= 1000 and 2 <= power <= 10):
        raise ValueError(
            "Invalid input\n"
            "needed_sum must be between 1 and 1000, power between 2 and 10."
        )

    return backtrack(needed_sum, power, 1, 0, 0)[1]  
