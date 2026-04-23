def minimum_subarray_sum(target: int, numbers: list[int]) -> int:
    if not numbers:
        return 0
    if target == 0 and target in numbers:
        return 0
    if not isinstance(numbers, (list, tuple)) or not all(
        isinstance(number, int) for number in numbers
    ):
        raise ValueError("numbers must be an iterable of integers")

    left = right = curr_sum = 0
    min_len = sys.maxsize

    while right < len(numbers):
        curr_sum += numbers[right]
        while curr_sum >= target and left <= right:
            min_len = min(min_len, right - left + 1)
            curr_sum -= numbers[left]
            left += 1
        right += 1

    return 0 if min_len == sys.maxsize else min_len
