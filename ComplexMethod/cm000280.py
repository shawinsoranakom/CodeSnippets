def interpolation_search(sorted_collection: list[int], item: int) -> int | None:
    """
    Searches for an item in a sorted collection by interpolation search algorithm.

    Args:
        sorted_collection: sorted list of integers
        item: item value to search

    Returns:
        int: The index of the found item, or None if the item is not found.
    Examples:
    >>> interpolation_search([1, 2, 3, 4, 5], 2)
    1
    >>> interpolation_search([1, 2, 3, 4, 5], 4)
    3
    >>> interpolation_search([1, 2, 3, 4, 5], 6) is None
    True
    >>> interpolation_search([], 1) is None
    True
    >>> interpolation_search([100], 100)
    0
    >>> interpolation_search([1, 2, 3, 4, 5], 0) is None
    True
    >>> interpolation_search([1, 2, 3, 4, 5], 7) is None
    True
    >>> interpolation_search([1, 2, 3, 4, 5], 2)
    1
    >>> interpolation_search([1, 2, 3, 4, 5], 0) is None
    True
    >>> interpolation_search([1, 2, 3, 4, 5], 7) is None
    True
    >>> interpolation_search([1, 2, 3, 4, 5], 2)
    1
    >>> interpolation_search([5, 5, 5, 5, 5], 3) is None
    True
    """
    left = 0
    right = len(sorted_collection) - 1

    while left <= right:
        # avoid divided by 0 during interpolation
        if sorted_collection[left] == sorted_collection[right]:
            if sorted_collection[left] == item:
                return left
            return None

        point = left + ((item - sorted_collection[left]) * (right - left)) // (
            sorted_collection[right] - sorted_collection[left]
        )

        # out of range check
        if point < 0 or point >= len(sorted_collection):
            return None

        current_item = sorted_collection[point]
        if current_item == item:
            return point
        if point < left:
            right = left
            left = point
        elif point > right:
            left = right
            right = point
        elif item < current_item:
            right = point - 1
        else:
            left = point + 1
    return None