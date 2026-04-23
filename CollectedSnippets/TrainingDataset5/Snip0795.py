def is_sum_subset(arr: list[int], required_sum: int) -> bool:
    arr_len = len(arr)
    subset = [[False] * (required_sum + 1) for _ in range(arr_len + 1)]

    for i in range(arr_len + 1):
        subset[i][0] = True

    for i in range(1, required_sum + 1):
        subset[0][i] = False

    for i in range(1, arr_len + 1):
        for j in range(1, required_sum + 1):
            if arr[i - 1] > j:
                subset[i][j] = subset[i - 1][j]
            if arr[i - 1] <= j:
                subset[i][j] = subset[i - 1][j] or subset[i - 1][j - arr[i - 1]]

    return subset[arr_len][required_sum]
