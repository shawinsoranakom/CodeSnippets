def quick_select(arr: list, target: int) -> int:
    """
    Two way partition the data into smaller and greater lists,
    in relationship to the pivot
    :param arr: The data to be searched (a list)
    :param target: The rank to be searched
    :return: element at rank target

    >>> quick_select([2, 4, 5, 7, 899, 54, 32], 5)
    32
    >>> quick_select([2, 4, 5, 7, 899, 54, 32], 1)
    2
    >>> quick_select([5, 4, 3, 2], 2)
    3
    >>> quick_select([3, 5, 7, 10, 2, 12], 3)
    5
    """

    # Invalid Input
    if target > len(arr):
        return -1

    # x is the estimated pivot by median of medians algorithm
    x = median_of_medians(arr)
    left = []
    right = []
    check = False
    for i in range(len(arr)):
        if arr[i] < x:
            left.append(arr[i])
        elif arr[i] > x:
            right.append(arr[i])
        elif arr[i] == x and not check:
            check = True
        else:
            right.append(arr[i])
    rank_x = len(left) + 1
    if rank_x == target:
        answer = x
    elif rank_x > target:
        answer = quick_select(left, target)
    elif rank_x < target:
        answer = quick_select(right, target - rank_x)
    return answer