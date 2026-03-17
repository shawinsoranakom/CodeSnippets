def largest_divisible_subset(items: list[int]) -> list[int]:
    items = sorted(items)

    number_of_items = len(items)

    memo = [1] * number_of_items
    hash_array = list(range(number_of_items))

    for i, item in enumerate(items):
        for prev_index in range(i):
            if ((items[prev_index] != 0 and item % items[prev_index]) == 0) and (
                (1 + memo[prev_index]) > memo[i]
            ):
                memo[i] = 1 + memo[prev_index]
                hash_array[i] = prev_index

    ans = -1
    last_index = -1

    for i, memo_item in enumerate(memo):
        if memo_item > ans:
            ans = memo_item
            last_index = i

    if last_index == -1:
        return []
    result = [items[last_index]]
    while hash_array[last_index] != last_index:
        last_index = hash_array[last_index]
        result.append(items[last_index])

    return result
