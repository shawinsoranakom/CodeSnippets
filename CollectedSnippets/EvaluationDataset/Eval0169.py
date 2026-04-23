def pairs_with_sum(arr: list, req_sum: int) -> int:

    return len([1 for a, b in combinations(arr, 2) if a + b == req_sum])
