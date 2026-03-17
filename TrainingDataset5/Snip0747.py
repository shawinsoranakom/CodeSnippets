def max_cross_sum(
    arr: Sequence[float], low: int, mid: int, high: int
) -> tuple[int, int, float]:
    left_sum, max_left = float("-inf"), -1
    right_sum, max_right = float("-inf"), -1

    summ: int | float = 0
    for i in range(mid, low - 1, -1):
        summ += arr[i]
        if summ > left_sum:
            left_sum = summ
            max_left = i

    summ = 0
    for i in range(mid + 1, high + 1):
        summ += arr[i]
        if summ > right_sum:
            right_sum = summ
            max_right = i

    return max_left, max_right, (left_sum + right_sum)
