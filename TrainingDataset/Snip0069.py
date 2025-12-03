def generate_all_combinations(n: int, k: int) -> list[list[int]]:
    
    if k < 0:
        raise ValueError("k must not be negative")
    if n < 0:
        raise ValueError("n must not be negative")

    result: list[list[int]] = []
    create_all_state(1, n, k, [], result)
    return result
