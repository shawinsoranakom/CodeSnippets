def kth_largest_element(arr: list[int], position: int) -> int:

    if not arr:
        return -1
    if not isinstance(position, int):
        raise ValueError("The position should be an integer")
    if not 1 <= position <= len(arr):
        raise ValueError("Invalid value of 'position'")
    low, high = 0, len(arr) - 1
    while low <= high:
        if low > len(arr) - 1 or high < 0:
            return -1
        pivot_index = partition(arr, low, high)
        if pivot_index == position - 1:
            return arr[pivot_index]
        elif pivot_index > position - 1:
            high = pivot_index - 1
        else:
            low = pivot_index + 1
    return -1
