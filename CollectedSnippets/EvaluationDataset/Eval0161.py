def find_triplets_with_0_sum(nums: list[int]) -> list[list[int]]:

    return [
        list(x)
        for x in sorted({abc for abc in combinations(sorted(nums), 3) if not sum(abc)})
    ]
