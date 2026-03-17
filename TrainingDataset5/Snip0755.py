def catalan_numbers(upper_limit: int) -> "list[int]":
    if upper_limit < 0:
        raise ValueError("Limit for the Catalan sequence must be ≥ 0")

    catalan_list = [0] * (upper_limit + 1)

    catalan_list[0] = 1
    if upper_limit > 0:
        catalan_list[1] = 1

    for i in range(2, upper_limit + 1):
        for j in range(i):
            catalan_list[i] += catalan_list[j] * catalan_list[i - j - 1]

    return catalan_list
